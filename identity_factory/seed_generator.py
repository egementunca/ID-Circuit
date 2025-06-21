"""
Seed generation system for identity circuit factory.
Generates identity circuits and stores them in dimension groups.
"""

import logging
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
import random
from sat_revsynth.circuit.circuit import Circuit
from sat_revsynth.synthesizers.circuit_synthesizer import CircuitSynthesizer
from .database import CircuitDatabase, CircuitRecord, DimGroupRecord, RepresentativeRecord

logger = logging.getLogger(__name__)

@dataclass
class SeedGenerationResult:
    """Result of seed generation process."""
    success: bool
    circuit_id: Optional[int] = None
    dim_group_id: Optional[int] = None
    representative_id: Optional[int] = None
    gate_composition: Optional[Tuple[int, int, int]] = None
    forward_gates: Optional[List[Tuple]] = None
    inverse_gates: Optional[List[Tuple]] = None
    identity_gates: Optional[List[Tuple]] = None
    permutation: Optional[List[int]] = None
    complexity_walk: Optional[List[int]] = None
    error_message: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None

class SeedGenerator:
    """Generates identity circuits using SAT-based synthesis."""
    
    def __init__(self, database: CircuitDatabase, max_inverse_gates: int = 40):
        self.database = database
        self.max_inverse_gates = max_inverse_gates
        self.generation_count = 0
        self.success_count = 0
        self.failure_count = 0
        self.total_generation_time = 0.0
        
        logger.info(f"SeedGenerator initialized with max_inverse_gates={max_inverse_gates}")
    
    def generate_seed(self, width: int, gate_count: int, 
                     max_attempts: int = 10,
                     sequential: bool = True) -> SeedGenerationResult:
        """
        Generate an identity circuit for the given dimensions.
        
        Args:
            width: Number of qubits
            gate_count: Number of gates in the forward circuit
            max_attempts: Maximum number of generation attempts
            sequential: Whether to use sequential gate generation
            
        Returns:
            SeedGenerationResult with the generated circuit information
        """
        import time
        start_time = time.time()
        
        logger.info(f"Generating seed for ({width}, {gate_count})")
        
        # Get or create dimension group
        dim_group = self.database.get_dim_group(width, gate_count)
        if not dim_group:
            dim_group = DimGroupRecord(
                id=None,
                width=width,
                gate_count=gate_count,
                circuit_count=0,
                is_processed=False
            )
            dim_group_id = self.database.store_dim_group(dim_group)
            dim_group.id = dim_group_id
        else:
            dim_group_id = dim_group.id
        
        # Attempt generation
        for attempt in range(max_attempts):
            try:
                result = self._attempt_generation(width, gate_count, sequential)
                if result.success:
                    # Store the circuit
                    circuit_record = CircuitRecord(
                        id=None,
                        width=width,
                        gate_count=gate_count,
                        gates=result.identity_gates,
                        permutation=result.permutation,
                        complexity_walk=result.complexity_walk
                    )
                    circuit_id = self.database.store_circuit(circuit_record)
                    
                    # Add circuit to dimension group
                    self.database.add_circuit_to_dim_group(dim_group_id, circuit_id)
                    
                    # Create representative if this is a new gate composition
                    gate_composition = result.gate_composition
                    existing_rep = self.database.get_representative_by_composition(dim_group_id, gate_composition)
                    
                    representative_id = None
                    if not existing_rep:
                        # This is a new gate composition, make it a representative
                        rep_record = RepresentativeRecord(
                            id=None,
                            dim_group_id=dim_group_id,
                            circuit_id=circuit_id,
                            gate_composition=gate_composition,
                            is_primary=True  # First one for this composition is primary
                        )
                        representative_id = self.database.store_representative(rep_record)
                        logger.info(f"Created new representative for composition {gate_composition}")
                    
                    # Update result with database IDs
                    result.circuit_id = circuit_id
                    result.dim_group_id = dim_group_id
                    result.representative_id = representative_id
                    
                    self.generation_count += 1
                    self.success_count += 1
                    
                    generation_time = time.time() - start_time
                    self.total_generation_time += generation_time
                    
                    logger.info(f"Successfully generated seed circuit {circuit_id} in {generation_time:.2f}s")
                    
                    result.metrics = {
                        'generation_time': generation_time,
                        'attempts': attempt + 1,
                        'gate_composition': gate_composition
                    }
                    
                    return result
                    
            except Exception as e:
                logger.warning(f"Generation attempt {attempt + 1} failed: {e}")
                continue
        
        # All attempts failed
        self.generation_count += 1
        self.failure_count += 1
        
        generation_time = time.time() - start_time
        self.total_generation_time += generation_time
        
        logger.error(f"Failed to generate seed for ({width}, {gate_count}) after {max_attempts} attempts")
        
        return SeedGenerationResult(
            success=False,
            error_message=f"Failed to generate after {max_attempts} attempts",
            metrics={'generation_time': generation_time, 'attempts': max_attempts}
        )
    
    def _attempt_generation(self, width: int, gate_count: int, 
                          sequential: bool) -> SeedGenerationResult:
        """Attempt to generate a single identity circuit."""
        try:
            # Generate forward circuit
            if sequential:
                forward_circuit = self._generate_sequential_circuit(width, gate_count)
            else:
                forward_circuit = self._generate_random_circuit(width, gate_count)
            
            forward_gates = forward_circuit.gates()
            
            # Generate inverse circuit
            inverse_circuit = self._generate_inverse_circuit(forward_circuit)
            inverse_gates = inverse_circuit.gates()
            
            # Combine to create identity
            identity_circuit = self._combine_circuits(forward_circuit, inverse_circuit)
            identity_gates = identity_circuit.gates()
            
            # Calculate gate composition
            gate_composition = self._calculate_gate_composition(identity_gates)
            
            # Generate complexity walk
            complexity_walk = self._generate_complexity_walk(identity_gates, width)
            
            # Get final permutation (should be identity)
            permutation = list(range(width))
            
            return SeedGenerationResult(
                success=True,
                gate_composition=gate_composition,
                forward_gates=forward_gates,
                inverse_gates=inverse_gates,
                identity_gates=identity_gates,
                permutation=permutation,
                complexity_walk=complexity_walk
            )
            
        except Exception as e:
            return SeedGenerationResult(
                success=False,
                error_message=str(e)
            )
    
    def _generate_sequential_circuit(self, width: int, gate_count: int) -> Circuit:
        """Generate a circuit using sequential gate synthesis."""
        # Use the CircuitSynthesizer from sat_revsynth
        # This needs to be implemented properly with the right parameters
        raise NotImplementedError("Sequential circuit generation needs CircuitSynthesizer setup")
    
    def _generate_random_circuit(self, width: int, gate_count: int) -> Circuit:
        """Generate a random circuit with the specified number of gates."""
        circuit = Circuit(width)
        
        for _ in range(gate_count):
            # Choose gate type randomly
            gate_type = random.choice(['NOT', 'CNOT', 'TOFFOLI'])
            
            if gate_type == 'NOT':
                target = random.randint(0, width - 1)
                circuit = circuit.x(target)
            elif gate_type == 'CNOT':
                control = random.randint(0, width - 1)
                target = random.randint(0, width - 1)
                while target == control:
                    target = random.randint(0, width - 1)
                circuit = circuit.cx(control, target)
            elif gate_type == 'TOFFOLI':
                if width >= 3:
                    qubits = random.sample(range(width), 3)
                    controls = qubits[:2]
                    target = qubits[2]
                    circuit = circuit.mcx(controls, target)
                else:
                    # Fall back to CNOT for small widths
                    control = random.randint(0, width - 1)
                    target = random.randint(0, width - 1)
                    while target == control:
                        target = random.randint(0, width - 1)
                    circuit = circuit.cx(control, target)
        
        return circuit
    
    def _generate_inverse_circuit(self, forward_circuit: Circuit) -> Circuit:
        """Generate the inverse of the forward circuit."""
        return forward_circuit.reverse()
    
    def _combine_circuits(self, forward: Circuit, inverse: Circuit) -> Circuit:
        """Combine forward and inverse circuits to create identity."""
        return forward + inverse
    
    def _calculate_gate_composition(self, gates: List[Tuple]) -> Tuple[int, int, int]:
        """Calculate the gate composition (n1, n2, n3) for NOT, CNOT, TOFFOLI gates."""
        not_count = 0
        cnot_count = 0
        toffoli_count = 0
        
        for controls, target in gates:
            if len(controls) == 0:
                not_count += 1
            elif len(controls) == 1:
                cnot_count += 1
            elif len(controls) == 2:
                toffoli_count += 1
            # For more than 2 controls, we could extend this or treat as multiple TOFFOLIs
        
        return (not_count, cnot_count, toffoli_count)
    
    def _generate_complexity_walk(self, gates: List[Tuple], width: int) -> List[int]:
        """Generate a complexity walk for the circuit."""
        # This is a simplified implementation
        return [len(gates)] * width
    
    def generate_multiple_seeds(self, width: int, gate_count: int, 
                              count: int = 1, **kwargs) -> List[SeedGenerationResult]:
        """Generate multiple seed circuits for the same dimensions."""
        results = []
        for i in range(count):
            logger.info(f"Generating seed {i+1}/{count} for ({width}, {gate_count})")
            result = self.generate_seed(width, gate_count, **kwargs)
            results.append(result)
            
            if not result.success:
                logger.warning(f"Failed to generate seed {i+1}/{count}")
        
        return results
    
    def get_generation_stats(self) -> Dict[str, Any]:
        """Get statistics about seed generation."""
        avg_time = self.total_generation_time / max(1, self.generation_count)
        success_rate = self.success_count / max(1, self.generation_count)
        
        return {
            'total_generations': self.generation_count,
            'successful_generations': self.success_count,
            'failed_generations': self.failure_count,
            'success_rate': success_rate,
            'total_generation_time': self.total_generation_time,
            'average_generation_time': avg_time,
            'width_range': 'Not tracked',  # Could be implemented
            'gate_count_range': 'Not tracked'  # Could be implemented
        } 