"""
Circuit unrolling system for identity circuit factory.
Generates equivalent circuits from representative circuits using various transformations.
"""

import logging
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass

from sat_revsynth.circuit.circuit import Circuit
from .database import CircuitDatabase, CircuitRecord, RepresentativeRecord

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
            unroll_types: List of unroll types to apply (e.g., 'sat_revsynth_unroll')
            
        Returns:
            UnrollResult with generation statistics
        """
        import time
        start_time = time.time()
        
        logger.info(f"Unrolling dimension group {dim_group_id}")
        
        dim_group = self.database.get_dim_group_by_id(dim_group_id)
        if not dim_group:
            return UnrollResult(success=False, error_message=f"Dimension group {dim_group_id} not found")
        
        representatives = self.database.get_representatives_for_dim_group(dim_group_id)
        if not representatives:
            return UnrollResult(success=False, error_message=f"No representatives for group {dim_group_id}")
        
        if unroll_types is None:
            unroll_types = ['sat_revsynth_unroll']
        
        total_new_circuits = 0
        unroll_type_counts = {ut: 0 for ut in unroll_types}
        
        for rep in representatives:
            circuit_record = self.database.get_circuit(rep.circuit_id)
            if not circuit_record:
                logger.warning(f"Circuit {rep.circuit_id} for representative {rep.id} not found")
                continue
            
            try:
                circuit = self._record_to_circuit(circuit_record)
                rep_result = self._perform_unrolling(circuit, rep, unroll_types)
                
                if rep_result.success:
                    total_new_circuits += rep_result.new_circuits
                    for ut, count in (rep_result.unroll_types or {}).items():
                        unroll_type_counts[ut] += count
                else:
                    logger.warning(f"Failed to unroll representative {rep.id}: {rep_result.error_message}")
            except Exception as e:
                logger.error(f"Critical failure processing representative {rep.id}: {e}")

        self.database.mark_dim_group_processed(dim_group_id)
        
        # Final stats update
        unroll_time = time.time() - start_time
        logger.info(f"Finished unrolling group {dim_group_id} in {unroll_time:.2f}s, generated {total_new_circuits} circuits.")
        
        return UnrollResult(
            success=True,
            dim_group_id=dim_group_id,
            total_equivalents=self.database.get_equivalent_count_for_dim_group(dim_group_id),
            new_circuits=total_new_circuits,
            unroll_types=unroll_type_counts
        )
    
    def _perform_unrolling(self, circuit: Circuit, representative: RepresentativeRecord, 
                          unroll_types: List[str]) -> UnrollResult:
        """Perform unrolling on a single representative using specified methods."""
        all_equivalents = []
        unroll_type_counts = {ut: 0 for ut in unroll_types}

        if 'sat_revsynth_unroll' in unroll_types:
            all_equivalents = circuit.unroll([])
            unroll_type_counts['sat_revsynth_unroll'] = len(all_equivalents)
        
        if len(all_equivalents) > self.max_equivalents:
            all_equivalents = all_equivalents[:self.max_equivalents]
        
        stored_count = 0
        for equiv_circuit in all_equivalents:
            try:
                circuit_id = self.database.store_equivalent_circuit(
                    original_circuit_id=representative.circuit_id,
                    gates=equiv_circuit.gates(),
                    width=equiv_circuit.width(),
                    permutation=list(range(equiv_circuit.width())),
                    unroll_type='sat_revsynth_unroll'
                )
                if circuit_id > 0:
                    stored_count += 1
            except Exception as e:
                logger.warning(f"Failed to store equivalent for rep {representative.id}: {e}")
        
        logger.info(f"Stored {stored_count} new equivalents for representative {representative.id}")
        return UnrollResult(success=True, new_circuits=stored_count, unroll_types=unroll_type_counts)

    def _record_to_circuit(self, record: CircuitRecord) -> Circuit:
        """Converts a CircuitRecord from the database to a sat_revsynth Circuit object."""
        try:
            if not isinstance(record.gates, list):
                raise TypeError(f"Malformed gates for circuit {record.id}: not a list.")

            circuit_gates = []
            for gate in record.gates:
                if isinstance(gate, (list, tuple)) and len(gate) == 2 and isinstance(gate[0], (list, tuple)) and isinstance(gate[1], int):
                    controls, target = gate
                    circuit_gates.append((list(controls), target))
                else:
                    raise TypeError(f"Malformed gate data in DB for circuit {record.id}: {gate}")
            
            # Use the constructor of the Circuit class
            new_circuit = Circuit(record.width)
            new_circuit._gates = circuit_gates
            new_circuit._tt = None # Invalidate truth table
            return new_circuit

        except Exception as e:
            logger.error(f"Failed to convert CircuitRecord {record.id} to Circuit object: {e}")
            raise

    def unroll_circuit(self, circuit_record: CircuitRecord, max_equivalents: int = 100) -> Dict[str, Any]:
        """
        Unroll a single circuit to generate all equivalent circuits.
        This uses the comprehensive unroll method from sat_revsynth which includes:
        - Swap space exploration (BFS)
        - Rotations
        - Reverse
        - Permutations
        """
        try:
            # Convert to sat_revsynth Circuit
            circuit = self._record_to_circuit(circuit_record)
            
            logger.info(f"Starting comprehensive unroll for circuit {circuit_record.id}")
            
            # Use the comprehensive unroll from sat_revsynth
            # This includes swap_space_bfs + rotations + reverse + permutations
            equivalent_circuits = circuit.unroll()
            
            logger.info(f"Unroll generated {len(equivalent_circuits)} total equivalents")
            
            # Check if we hit the limit (meaning we might not have ALL equivalents)
            hit_limit = len(equivalent_circuits) >= max_equivalents
            
            # Limit the number of equivalents if specified
            if hit_limit:
                logger.info(f"Limiting equivalents from {len(equivalent_circuits)} to {max_equivalents}")
                equivalent_circuits = equivalent_circuits[:max_equivalents]
            
            # Convert circuits back to gate lists
            equivalents_as_gates = []
            for equiv_circuit in equivalent_circuits:
                gates = equiv_circuit.gates()
                if gates != circuit_record.gates:  # Don't include the original circuit
                    equivalents_as_gates.append(gates)
            
            result = {
                'success': True,
                'equivalents': equivalents_as_gates,
                'total_generated': len(equivalent_circuits),
                'unique_equivalents': len(equivalents_as_gates),
                'original_excluded': len(equivalent_circuits) - len(equivalents_as_gates),
                'fully_unrolled': not hit_limit,  # True if we didn't hit the limit
                'unroll_types': {
                    'comprehensive': len(equivalent_circuits)
                }
            }
            
            # Clean up other representatives with the same composition
            gate_composition = self.database._calculate_gate_composition(circuit_record.gates)
            converted_count = self.database.cleanup_representatives_after_unroll(
                circuit_record.dim_group_id, 
                gate_composition, 
                circuit_record.id,
                equivalents_as_gates
            )
            
            result['representatives_converted'] = converted_count
            
            # If we fully unrolled without hitting limits, mark this representative as fully unrolled
            if not hit_limit:
                # Get the representative record for this circuit
                representatives = self.database.get_representatives_by_composition(
                    circuit_record.dim_group_id, gate_composition
                )
                rep_for_circuit = next(
                    (rep for rep in representatives if rep.circuit_id == circuit_record.id), 
                    None
                )
                if rep_for_circuit:
                    self.database.mark_representative_fully_unrolled(rep_for_circuit.id)
                    result['representative_marked_fully_unrolled'] = True
            
            return result
            
        except Exception as e:
            logger.error(f"Unroll failed for circuit {circuit_record.id}: {e}")
            return {
                'success': False,
                'error': str(e),
                'equivalents': []
            }
    
    def get_unroll_stats(self) -> Dict[str, Any]:
        """Get statistics about unrolling operations."""
        return {
            "total_unroll_time": self.total_unroll_time,
            "circuits_unrolled": self.circuits_unrolled,
            "total_equivalents_generated": self.total_equivalents_generated,
            "average_unroll_time": self.total_unroll_time / max(1, self.circuits_unrolled),
            "average_equivalents_per_circuit": self.total_equivalents_generated / max(1, self.circuits_unrolled)
        } 