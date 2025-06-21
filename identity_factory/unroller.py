"""
Circuit unrolling system for identity circuit factory.
Generates equivalent circuits from representative circuits using various transformations.
"""

import logging
from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from itertools import permutations
from sat_revsynth.circuit.circuit import Circuit
from .database import CircuitDatabase, CircuitRecord, EquivalentRecord, RepresentativeRecord

logger = logging.getLogger(__name__)

@dataclass
class UnrollResult:
    """Result of unrolling operation."""
    success: bool
    dim_group_id: Optional[int] = None
    total_equivalents: int = 0
    new_circuits: int = 0
    unroll_types: Optional[Dict[str, int]] = None
    error_message: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None

class CircuitUnroller:
    """Unrolls representative circuits to generate equivalent circuits."""
    
    def __init__(self, database: CircuitDatabase, max_equivalents: int = 10000):
        self.database = database
        self.max_equivalents = max_equivalents
        self.unroll_count = 0
        self.total_unroll_time = 0.0
        self.unroll_stats = {
            'total_unrolled': 0,
            'average_equivalents_per_group': 0.0,
            'largest_group': 0,
            'smallest_group': float('inf')
        }
        
        logger.info(f"CircuitUnroller initialized with max_equivalents={max_equivalents}")
    
    def unroll_dimension_group(self, dim_group_id: int, 
                              unroll_types: Optional[List[str]] = None) -> UnrollResult:
        """
        Unroll all representatives in a dimension group to generate equivalent circuits.
        
        Args:
            dim_group_id: ID of the dimension group to unroll
            unroll_types: List of unroll types to apply (swap, rotation, permutation, etc.)
            
        Returns:
            UnrollResult with generation statistics
        """
        import time
        start_time = time.time()
        
        logger.info(f"Unrolling dimension group {dim_group_id}")
        
        # Get dimension group info
        dim_group = self.database.get_dim_group_by_id(dim_group_id)
        if not dim_group:
            return UnrollResult(
                success=False,
                error_message=f"Dimension group {dim_group_id} not found"
            )
        
        # Get all representatives for this dimension group
        representatives = self.database.get_representatives_for_dim_group(dim_group_id)
        if not representatives:
            return UnrollResult(
                success=False,
                error_message=f"No representatives found for dimension group {dim_group_id}"
            )
        
        # Default unroll types
        if unroll_types is None:
            unroll_types = ['swap', 'rotation', 'permutation', 'reverse']
        
        total_new_circuits = 0
        unroll_type_counts = {ut: 0 for ut in unroll_types}
        
        # Unroll each representative
        for rep in representatives:
            logger.info(f"Unrolling representative {rep.id} with composition {rep.gate_composition}")
            
            # Get the representative circuit
            circuit_record = self.database.get_circuit(rep.circuit_id)
            if not circuit_record:
                logger.warning(f"Circuit {rep.circuit_id} not found for representative {rep.id}")
                continue
            
            # Convert to Circuit object
            circuit = self._record_to_circuit(circuit_record)
            
            # Perform unrolling
            rep_result = self._perform_unrolling(circuit, rep, unroll_types)
            
            if rep_result.success:
                total_new_circuits += rep_result.new_circuits
                if rep_result.unroll_types:
                    for ut, count in rep_result.unroll_types.items():
                        unroll_type_counts[ut] += count
            else:
                logger.warning(f"Failed to unroll representative {rep.id}: {rep_result.error_message}")
        
        # Mark dimension group as processed
        self.database.mark_dim_group_processed(dim_group_id)
        
        # Update stats
        self.unroll_count += 1
        unroll_time = time.time() - start_time
        self.total_unroll_time += unroll_time
        
        # Get total equivalents count
        total_equivalents = len(self.database.get_all_equivalents_for_dim_group(dim_group_id))
        
        # Update unroll stats
        self.unroll_stats['total_unrolled'] += 1
        self.unroll_stats['largest_group'] = max(self.unroll_stats['largest_group'], total_equivalents)
        if self.unroll_stats['smallest_group'] == float('inf'):
            self.unroll_stats['smallest_group'] = total_equivalents
        else:
            self.unroll_stats['smallest_group'] = min(self.unroll_stats['smallest_group'], total_equivalents)
        
        self.unroll_stats['average_equivalents_per_group'] = (
            (self.unroll_stats['average_equivalents_per_group'] * (self.unroll_stats['total_unrolled'] - 1) + total_equivalents) /
            self.unroll_stats['total_unrolled']
        )
        
        logger.info(f"Unrolled dimension group {dim_group_id}: {total_new_circuits} new circuits, {total_equivalents} total equivalents")
        
        return UnrollResult(
            success=True,
            dim_group_id=dim_group_id,
            total_equivalents=total_equivalents,
            new_circuits=total_new_circuits,
            unroll_types=unroll_type_counts,
            metrics={
                'unroll_time': unroll_time,
                'representatives_processed': len(representatives),
                'unroll_types_used': unroll_types
            }
        )
    
    def _perform_unrolling(self, circuit: Circuit, representative: RepresentativeRecord, 
                          unroll_types: List[str]) -> UnrollResult:
        """Perform unrolling operations on a single representative circuit."""
        try:
            all_equivalents = []
            unroll_type_counts = {ut: 0 for ut in unroll_types}
            
            # Apply each unroll type
            for unroll_type in unroll_types:
                if len(all_equivalents) >= self.max_equivalents:
                    break
                
                if unroll_type == 'swap':
                    equivalents = self._swap_unroll(circuit)
                elif unroll_type == 'rotation':
                    equivalents = self._rotation_unroll(circuit)
                elif unroll_type == 'permutation':
                    equivalents = self._permutation_unroll(circuit)
                elif unroll_type == 'reverse':
                    equivalents = self._reverse_unroll(circuit)
                elif unroll_type == 'local_unroll':
                    equivalents = self._local_unroll(circuit)
                elif unroll_type == 'full_unroll':
                    equivalents = self._full_unroll(circuit)
                else:
                    logger.warning(f"Unknown unroll type: {unroll_type}")
                    continue
                
                # Store unique equivalents
                for equiv_circuit in equivalents:
                    if len(all_equivalents) >= self.max_equivalents:
                        break
                    
                    # Store the equivalent circuit
                    equiv_record = CircuitRecord(
                        id=None,
                        width=equiv_circuit.width(),
                        gate_count=len(equiv_circuit.gates()),
                        gates=equiv_circuit.gates(),
                        permutation=list(range(equiv_circuit.width()))  # Simplified
                    )
                    
                    equiv_circuit_id = self.database.store_circuit(equiv_record)
                    
                    # Store the equivalent relationship
                    equiv_relation = EquivalentRecord(
                        id=None,
                        circuit_id=equiv_circuit_id,
                        representative_id=representative.id,
                        unroll_type=unroll_type,
                        unroll_params={'method': unroll_type}
                    )
                    
                    self.database.store_equivalent(equiv_relation)
                    
                    all_equivalents.append(equiv_circuit)
                    unroll_type_counts[unroll_type] += 1
            
            return UnrollResult(
                success=True,
                new_circuits=len(all_equivalents),
                unroll_types=unroll_type_counts
            )
            
        except Exception as e:
            logger.error(f"Unrolling failed for representative {representative.id}: {e}")
            return UnrollResult(
                success=False,
                error_message=str(e)
            )
    
    def _swap_unroll(self, circuit: Circuit) -> List[Circuit]:
        """Generate equivalents using gate swapping."""
        try:
            # Use the swap space exploration from sat_revsynth
            swap_space = circuit.swap_space_dfs()
            return swap_space[:min(len(swap_space), 100)]  # Limit to prevent explosion
        except Exception as e:
            logger.warning(f"Swap unroll failed: {e}")
            return []
    
    def _rotation_unroll(self, circuit: Circuit) -> List[Circuit]:
        """Generate equivalents using circuit rotations."""
        try:
            rotations = circuit.rotations()
            return rotations[:min(len(rotations), 50)]
        except Exception as e:
            logger.warning(f"Rotation unroll failed: {e}")
            return []
    
    def _permutation_unroll(self, circuit: Circuit) -> List[Circuit]:
        """Generate equivalents using qubit permutations."""
        try:
            permutations_list = circuit.permutations()
            return permutations_list[:min(len(permutations_list), 50)]
        except Exception as e:
            logger.warning(f"Permutation unroll failed: {e}")
            return []
    
    def _reverse_unroll(self, circuit: Circuit) -> List[Circuit]:
        """Generate equivalents using circuit reversal."""
        try:
            reversed_circuit = circuit.reverse()
            return [reversed_circuit]
        except Exception as e:
            logger.warning(f"Reverse unroll failed: {e}")
            return []
    
    def _local_unroll(self, circuit: Circuit) -> List[Circuit]:
        """Generate equivalents using local transformations."""
        try:
            # This would implement local gate optimizations
            # For now, return empty list as placeholder
            return []
        except Exception as e:
            logger.warning(f"Local unroll failed: {e}")
            return []
    
    def _full_unroll(self, circuit: Circuit) -> List[Circuit]:
        """Generate the complete unroll space."""
        try:
            # Use the full unroll method from sat_revsynth
            full_unroll = circuit.unroll()
            return full_unroll[:min(len(full_unroll), 200)]  # Limit to prevent explosion
        except Exception as e:
            logger.warning(f"Full unroll failed: {e}")
            return []
    
    def _record_to_circuit(self, record: CircuitRecord) -> Circuit:
        """Convert a CircuitRecord to a Circuit object."""
        circuit = Circuit(record.width)
        
        for gate in record.gates:
            controls, target = gate
            if len(controls) == 0:
                circuit = circuit.x(target)
            elif len(controls) == 1:
                circuit = circuit.cx(controls[0], target)
            elif len(controls) == 2:
                circuit = circuit.mcx(controls, target)
            else:
                # Handle multi-controlled gates
                circuit = circuit.mcx(controls, target)
        
        return circuit
    
    def unroll_all_dimension_groups(self, unroll_types: Optional[List[str]] = None) -> Dict[int, UnrollResult]:
        """Unroll all unprocessed dimension groups."""
        unprocessed_groups = self.database.get_unprocessed_dim_groups()
        results = {}
        
        logger.info(f"Unrolling {len(unprocessed_groups)} dimension groups")
        
        for dim_group in unprocessed_groups:
            logger.info(f"Processing dimension group {dim_group.id}: ({dim_group.width}, {dim_group.gate_count})")
            result = self.unroll_dimension_group(dim_group.id, unroll_types)
            results[dim_group.id] = result
        
        return results
    
    def get_unroll_stats(self) -> Dict[str, Any]:
        """Get statistics about unrolling operations."""
        return self.unroll_stats.copy() 