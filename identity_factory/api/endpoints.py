"""
API endpoints for the Identity Circuit Factory.
Provides REST API for generating, retrieving, and managing identity circuits.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import JSONResponse
import asyncio
import json

from .models import (
    CircuitRequest, GenerationResultResponse, 
    DimGroupResponse, CircuitResponse,
    FactoryStatsResponse, DimGroupAnalysisResponse,
    BatchCircuitRequest, UnrollResultResponse,
    RepresentativeCircuitResponse, CircuitASCIIRepresentation,
    EnhancedCircuitDetailsResponse
)
from ..factory_manager import IdentityFactory, FactoryConfig
from ..database import CircuitDatabase

logger = logging.getLogger(__name__)

# Global factory instance
_factory: Optional[IdentityFactory] = None

def get_factory() -> IdentityFactory:
    """Get or create the global factory instance."""
    global _factory
    if _factory is None:
        config = FactoryConfig()
        _factory = IdentityFactory(config)
    return _factory

# Create router
router = APIRouter(tags=["identity-circuits"])

@router.post("/generate", response_model=GenerationResultResponse)
async def generate_circuit(
    request: CircuitRequest,
    background_tasks: BackgroundTasks,
    factory: IdentityFactory = Depends(get_factory)
) -> GenerationResultResponse:
    """
    Generate an identity circuit for specified dimensions.
    
    Args:
        request: Generation parameters
        background_tasks: FastAPI background tasks
        factory: Factory instance
        
    Returns:
        Generation result with circuit information
    """
    try:
        logger.info(f"API: Generating circuit ({request.width}, {request.gate_count})")
        
        # Generate circuit
        result = factory.generate_identity_circuit(
            width=request.width,
            gate_count=request.gate_count,
            enable_unrolling=request.enable_unrolling,
            enable_post_processing=request.enable_post_processing,
            enable_debris_analysis=request.enable_debris_analysis,
            enable_ml_analysis=request.enable_ml_analysis,
            use_job_queue=request.use_job_queue,
            sequential=request.sequential
        )
        
        if not result['success']:
            raise HTTPException(
                status_code=500, 
                detail=f"Generation failed: {result.get('error', 'Unknown error')}"
            )
        
        # Extract key information
        seed_result = result.get('seed_generation')
        circuit_id = seed_result.circuit_id if seed_result else None
        dim_group_id = seed_result.dim_group_id if seed_result else None
        representative_id = getattr(seed_result, 'representative_id', None) if seed_result else None
        
        # If dimension group ID is still None, try to get it from the circuit
        if circuit_id and not dim_group_id:
            try:
                circuit = factory.db.get_circuit(circuit_id)
                if circuit:
                    dim_group_id = circuit.dim_group_id
            except Exception as e:
                logger.warning(f"Could not get dimension group from circuit {circuit_id}: {e}")
        
        # Get equivalents count
        equivalents_count = 0
        if 'unrolling' in result and isinstance(result['unrolling'], dict):
            equivalents_count = result['unrolling'].get('total_equivalents', 0)
        
        return GenerationResultResponse(
            success=True,
            width=request.width,
            length=request.gate_count,
            seed_circuit_id=circuit_id,
            dim_group_id=dim_group_id,
            total_equivalents=equivalents_count,
            total_time=result.get('total_time', 0.0)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dim-groups", response_model=List[DimGroupResponse])
async def list_dimension_groups(
    width: Optional[int] = Query(None, description="Filter by width"),
    length: Optional[int] = Query(None, description="Filter by gate count"),
    processed_only: bool = Query(False, description="Only processed groups"),
    factory: IdentityFactory = Depends(get_factory)
) -> List[DimGroupResponse]:
    """
    List dimension groups with optional filtering.
    
    Args:
        width: Optional width filter
        gate_count: Optional gate count filter
        processed_only: Only return processed groups
        factory: Factory instance
        
    Returns:
        List of dimension groups
    """
    try:
        db = factory.db
        
        # Get dimension groups with filtering
        if width and length:
            dim_group = db.get_dim_group(width, length)
            dim_groups = [dim_group] if dim_group else []
        elif width:
            dim_groups = [dg for dg in db.get_all_dim_groups() if dg.width == width]
        else:
            dim_groups = db.get_all_dim_groups()
        
        # Filter processed if requested
        if processed_only:
            dim_groups = [dg for dg in dim_groups if dg.is_processed]
        
        # Convert to response format
        responses = []
        for dg in dim_groups:
            # Get true representatives (only those that are still representatives)
            representatives = db.get_true_representatives_for_dim_group(dg.id)
            
            # Get equivalents count
            equivalents = db.get_all_equivalents_for_dim_group(dg.id)
            
            responses.append(DimGroupResponse(
                id=dg.id,
                width=dg.width,
                length=dg.gate_count,
                circuit_count=dg.circuit_count,
                is_processed=dg.is_processed,
                total_equivalents=len(equivalents)
            ))
        
        return responses
        
    except Exception as e:
        logger.error(f"API list dimension groups failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dimension-groups/{dim_group_id}", response_model=DimGroupResponse)
async def get_dimension_group(
    dim_group_id: int,
    factory: IdentityFactory = Depends(get_factory)
) -> DimGroupResponse:
    """
    Get detailed information about a specific dimension group.
    
    Args:
        dim_group_id: Dimension group ID
        factory: Factory instance
        
    Returns:
        Dimension group details
    """
    try:
        db = factory.db
        
        # Get dimension group
        dim_group = db.get_dim_group_by_id(dim_group_id)
        if not dim_group:
            raise HTTPException(status_code=404, detail="Dimension group not found")
        
        # Get representatives
        representatives = db.get_representatives_for_dim_group(dim_group_id)
        
        # Get equivalents
        equivalents = db.get_all_equivalents_for_dim_group(dim_group_id)
        
        return DimGroupResponse(
            id=dim_group.id,
            width=dim_group.width,
            length=dim_group.gate_count,
            circuit_count=dim_group.circuit_count,
            is_processed=dim_group.is_processed,
            total_equivalents=len(equivalents)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API get dimension group failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/circuits/{circuit_id}", response_model=CircuitResponse)
async def get_circuit(
    circuit_id: int,
    factory: IdentityFactory = Depends(get_factory)
) -> CircuitResponse:
    """
    Get detailed information about a specific circuit.
    
    Args:
        circuit_id: Circuit ID
        factory: Factory instance
        
    Returns:
        Circuit details
    """
    try:
        db = factory.db
        
        # Get circuit
        circuit = db.get_circuit(circuit_id)
        if not circuit:
            raise HTTPException(status_code=404, detail="Circuit not found")
        
        return CircuitResponse(
            id=circuit.id,
            width=circuit.width,
            length=circuit.gate_count,
            gates=circuit.gates,
            permutation=circuit.permutation
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API get circuit failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dim-groups/{dim_group_id}/representatives")
async def get_representatives_for_dim_group(
    dim_group_id: int,
    factory: IdentityFactory = Depends(get_factory)
) -> List[RepresentativeCircuitResponse]:
    """
    Get all representative circuits for a dimension group, grouped by gate composition.
    
    Args:
        dim_group_id: Dimension group ID
        factory: Factory instance
        
    Returns:
        List of representative circuits with their details, one per unique gate composition
    """
    try:
        import sqlite3
        db = factory.db
        
        # Check if dimension group exists
        dim_group = db.get_dim_group_by_id(dim_group_id)
        if not dim_group:
            raise HTTPException(status_code=404, detail="Dimension group not found")
        
        # Get unique gate compositions and their representative counts
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.execute("""
                SELECT r.gate_composition, 
                       COUNT(DISTINCT r.circuit_id) as composition_count,
                       MIN(r.circuit_id) as primary_circuit_id
                FROM representatives r
                JOIN circuits c ON r.circuit_id = c.id
                WHERE r.dim_group_id = ? AND c.representative_id = c.id
                GROUP BY r.gate_composition
                ORDER BY primary_circuit_id
            """, (dim_group_id,))
            
            result = []
            for row in cursor.fetchall():
                gate_composition_json, composition_count, primary_circuit_id = row
                gate_composition = json.loads(gate_composition_json)
                
                # Get the primary circuit details
                circuit = db.get_circuit(primary_circuit_id)
                if circuit:
                    # Calculate total equivalents for this composition
                    equiv_cursor = conn.execute("""
                        SELECT COUNT(*) FROM circuits c
                        JOIN representatives r ON c.representative_id = r.circuit_id
                        WHERE r.dim_group_id = ? AND r.gate_composition = ? AND c.representative_id != c.id
                    """, (dim_group_id, gate_composition_json))
                    total_equivalents = equiv_cursor.fetchone()[0]
                    
                    # Get the representative record to check if it's fully unrolled
                    rep_cursor = conn.execute("""
                        SELECT fully_unrolled FROM representatives 
                        WHERE dim_group_id = ? AND circuit_id = ? AND gate_composition = ?
                    """, (dim_group_id, primary_circuit_id, gate_composition_json))
                    rep_row = rep_cursor.fetchone()
                    fully_unrolled = bool(rep_row[0]) if rep_row else False
                    
                    result.append(RepresentativeCircuitResponse(
                        circuit=CircuitResponse(
                            id=circuit.id,
                            width=circuit.width,
                            length=circuit.gate_count,
                            gates=circuit.gates,
                            permutation=circuit.permutation
                        ),
                        gate_composition=tuple(gate_composition),
                        composition_count=composition_count,
                        total_equivalents=total_equivalents,
                        fully_unrolled=fully_unrolled
                    ))
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API get representatives failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _calculate_gate_composition(gates: List[Tuple]) -> Tuple[int, int, int]:
    """Calculate gate composition (NOT, CNOT, CCNOT counts)."""
    not_count = cnot_count = ccnot_count = 0
    
    for gate in gates:
        controls, target = gate
        control_count = len(controls)
        if control_count == 0:
            not_count += 1
        elif control_count == 1:
            cnot_count += 1
        elif control_count == 2:
            ccnot_count += 1
    
    return (not_count, cnot_count, ccnot_count)

@router.get("/dim-groups/{dim_group_id}/compositions/{composition}/circuits")
async def get_circuits_by_composition(
    dim_group_id: int,
    composition: str,
    factory: IdentityFactory = Depends(get_factory)
) -> List[CircuitResponse]:
    """
    Get representative circuits for a specific gate composition within a dimension group.
    Only shows circuits that are representatives (representative_id == circuit_id).
    
    Args:
        dim_group_id: Dimension group ID
        composition: Gate composition as "NOT,CNOT,CCNOT" (e.g., "8,6,4")
        factory: Factory instance
        
    Returns:
        List of representative circuits with the specified gate composition
    """
    try:
        import sqlite3
        db = factory.db
        
        # Parse the composition
        try:
            not_count, cnot_count, ccnot_count = map(int, composition.split(','))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid composition format. Expected 'NOT,CNOT,CCNOT'")
        
        gate_composition = [not_count, cnot_count, ccnot_count]
        
        with sqlite3.connect(db.db_path) as conn:
            # Get circuits that are representatives with this composition, including fully_unrolled status
            cursor = conn.execute("""
                SELECT DISTINCT c.id, c.width, c.gate_count, c.gates, c.permutation, 
                       c.complexity_walk, c.circuit_hash, c.representative_id, r.fully_unrolled
                FROM circuits c
                JOIN dim_group_circuits dgc ON c.id = dgc.circuit_id
                JOIN representatives r ON c.id = r.circuit_id
                WHERE dgc.dim_group_id = ? 
                  AND r.gate_composition = ?
                  AND c.representative_id = c.id
                ORDER BY c.id
            """, (dim_group_id, json.dumps(gate_composition)))
            
            circuits = []
            for row in cursor.fetchall():
                circuit_id, width, gate_count, gates_json, permutation_json, complexity_walk_json, circuit_hash, representative_id, fully_unrolled = row
                
                # Parse JSON fields
                gates = json.loads(gates_json) if gates_json else []
                permutation = json.loads(permutation_json) if permutation_json else []
                complexity_walk = json.loads(complexity_walk_json) if complexity_walk_json else None
                
                circuits.append(CircuitResponse(
                    id=circuit_id,
                    width=width,
                    length=gate_count,
                    gates=gates,
                    permutation=permutation,
                    complexity_walk=complexity_walk,
                    circuit_hash=circuit_hash,
                    is_representative=True,  # All circuits in this view are representatives
                    representative_id=representative_id,
                    fully_unrolled=bool(fully_unrolled)
                ))
            
            return circuits
            
    except Exception as e:
        logger.error(f"Error fetching circuits by composition: {e}")
        raise HTTPException(status_code=500, detail=f"Error fetching circuits: {str(e)}")

@router.post("/circuits/{circuit_id}/unroll")
async def unroll_circuit(
    circuit_id: int,
    max_equivalents: Optional[int] = Query(100, description="Maximum equivalents to generate"),
    check_existing: bool = Query(True, description="Check and merge existing sub-seeds"),
    factory: IdentityFactory = Depends(get_factory)
) -> Dict[str, Any]:
    """
    Unroll a circuit to generate equivalents and manage sub-seed relationships.
    
    Args:
        circuit_id: Circuit ID to unroll
        max_equivalents: Maximum number of equivalents to generate
        check_existing: Whether to check and merge existing sub-seeds
        factory: Factory instance
        
    Returns:
        Unroll results with equivalents and merged sub-seeds
    """
    try:
        db = factory.db
        
        # Get the circuit to unroll
        circuit = db.get_circuit(circuit_id)
        if not circuit:
            raise HTTPException(status_code=404, detail="Circuit not found")
        
        logger.info(f"API: Unrolling circuit {circuit_id} (max_equivalents={max_equivalents})")
        
        # Now that CircuitRecord has dim_group_id, we can access it directly
        dim_group_id = circuit.dim_group_id
        if not dim_group_id:
            raise HTTPException(status_code=404, detail="Circuit not associated with any dimension group")
        
        dim_group = db.get_dim_group_by_id(dim_group_id)
        if not dim_group:
            raise HTTPException(status_code=404, detail="Dimension group not found")
        
        # Perform the unroll operation
        unroll_result = await _perform_circuit_unroll(
            factory, circuit, dim_group_id, max_equivalents, check_existing
        )
        
        return {
            "success": True,
            "circuit_id": circuit_id,
            "dim_group_id": dim_group_id,
            "equivalents_generated": unroll_result["equivalents_count"],
            "sub_seeds_merged": unroll_result["merged_count"],
            "new_representative_id": unroll_result.get("representative_id", circuit_id),
            "total_time": unroll_result["total_time"],
            "message": unroll_result["message"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        full_traceback = traceback.format_exc()
        logger.error(f"API unroll circuit failed: {e}")
        logger.error(f"Full traceback: {full_traceback}")
        
        # Print to console as well for debugging
        print(f"UNROLL ERROR: {e}")
        print(f"FULL TRACEBACK:\n{full_traceback}")
        
        raise HTTPException(status_code=500, detail=str(e))

async def _perform_circuit_unroll(factory, circuit, dim_group_id: int, max_equivalents: int, check_existing: bool) -> Dict[str, Any]:
    """
    Perform the actual unroll operation with sub-seed management.
    """
    import time
    start_time = time.time()
    
    db = factory.db
    unroller = factory.unroller
    
    # Step 1: Generate equivalents for the circuit
    logger.info(f"Generating equivalents for circuit {circuit.id}")
    logger.debug(f"About to call unroller.unroll_circuit with circuit {circuit}")
    logger.debug(f"Unroller type: {type(unroller)}")
    logger.debug(f"Circuit type: {type(circuit)}")
    logger.debug(f"Has dim_group_id attr: {hasattr(circuit, 'dim_group_id')}")
    try:
        unroll_results = unroller.unroll_circuit(circuit, max_equivalents=max_equivalents)
        logger.debug(f"Unroll results: {unroll_results}")
        equivalents = unroll_results.get('equivalents', [])
        logger.info(f"Generated {len(equivalents)} equivalents")
    except Exception as e:
        logger.error(f"Unroll generation failed: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return {
            "equivalents_count": 0,
            "merged_count": 0,
            "total_time": time.time() - start_time,
            "message": f"Unroll failed: {str(e)}"
        }
    
    merged_count = 0
    
    if check_existing and equivalents:
        # Step 2: Get all circuits in the same dimension group with same gate composition
        circuit_composition = _calculate_gate_composition(circuit.gates)
        all_circuits = db.get_circuits_in_dim_group(dim_group_id)
        
        # Find potential sub-seeds to check
        potential_sub_seeds = []
        for other_circuit in all_circuits:
            if (other_circuit.id != circuit.id and 
                _calculate_gate_composition(other_circuit.gates) == circuit_composition):
                potential_sub_seeds.append(other_circuit)
        
        logger.info(f"Found {len(potential_sub_seeds)} potential sub-seeds to check")
        
        # Step 3: Check if any equivalents match existing sub-seeds
        for sub_seed in potential_sub_seeds:
            for equivalent in equivalents:
                # Handle different equivalent formats
                if isinstance(equivalent, dict):
                    equivalent_gates = equivalent.get('gates', [])
                elif isinstance(equivalent, list):
                    equivalent_gates = equivalent
                else:
                    # Assume it's the gates directly
                    equivalent_gates = equivalent
                
                if _circuits_are_equivalent(sub_seed.gates, equivalent_gates):
                    logger.info(f"Sub-seed {sub_seed.id} matches equivalent - converting to equivalent")
                    # TODO: Fix convert_circuit_to_equivalent to work with circuit IDs
                    # DISABLED: This was causing sub-seeds to disappear when unrolled
                    logger.debug(f"Would convert sub-seed {sub_seed.id} to equivalent of {circuit.id}")
                    merged_count += 1
                    break
    
    # Step 4: Store the generated equivalents in database
    stored_equivalents = 0
    for equivalent in equivalents:
        try:
            # Extract data from the unroller result structure 
            if isinstance(equivalent, dict):
                gates = equivalent.get('gates', [])
                permutation = equivalent.get('permutation', circuit.permutation)
            else:
                # Fallback for other formats
                gates = equivalent
                permutation = circuit.permutation
            
            # If gates is a dictionary (incorrect format), extract the actual gates
            if isinstance(gates, dict):
                permutation = gates.get('permutation', permutation)  # Get permutation from dict if available
                gates = gates.get('gates', [])  # Extract actual gates from dict
            
            # Store as equivalent of the original circuit
            db.store_equivalent_circuit(
                original_circuit_id=circuit.id,
                gates=gates,
                width=circuit.width,
                permutation=permutation
            )
            stored_equivalents += 1
        except Exception as e:
            logger.warning(f"Failed to store equivalent: {e}")
            logger.debug(f"Equivalent data: {equivalent}")
    
    total_time = time.time() - start_time
    
    # Step 5: Update circuit as representative if it now has equivalents
    if stored_equivalents > 0 or merged_count > 0:
        db.update_circuit_as_representative(circuit.id)
        logger.info(f"Circuit {circuit.id} updated as representative")
    
    message = f"Generated {stored_equivalents} new equivalents, merged {merged_count} existing sub-seeds"
    
    return {
        "equivalents_count": stored_equivalents,
        "merged_count": merged_count,
        "representative_id": circuit.id,
        "total_time": total_time,
        "message": message
    }

def _circuits_are_equivalent(gates1: List[Tuple], gates2: List[Tuple]) -> bool:
    """
    Check if two circuits are equivalent (same gates in same order).
    This is a basic implementation - could be enhanced with more sophisticated equivalence checking.
    """
    if len(gates1) != len(gates2):
        return False
    
    return gates1 == gates2

@router.get("/circuits/{circuit_id}/equivalents")
async def get_circuit_equivalents(
    circuit_id: int,
    factory: IdentityFactory = Depends(get_factory)
) -> List[CircuitResponse]:
    """
    Get all equivalent circuits for a given circuit.
    
    Args:
        circuit_id: Circuit ID
        factory: Factory instance
        
    Returns:
        List of equivalent circuits
    """
    try:
        db = factory.db
        
        # Get the circuit
        circuit = db.get_circuit(circuit_id)
        if not circuit:
            raise HTTPException(status_code=404, detail="Circuit not found")
        
        # Get equivalents
        equivalents = db.get_equivalents_for_circuit(circuit_id)
        
        result = []
        for equiv in equivalents:
            try:
                # Handle both correct gates format and dictionary format
                gates = equiv.gates
                permutation = equiv.permutation
                
                # If gates is a dictionary (incorrect format), extract the actual gates
                if isinstance(gates, dict):
                    permutation = gates.get('permutation', permutation)  # Get permutation from dict if available
                    gates = gates.get('gates', [])  # Extract actual gates from dict
                
                # Ensure gates is a list
                if not isinstance(gates, list):
                    logger.warning(f"Circuit {equiv.id} has invalid gates format: {type(gates)}")
                    continue
                
                # Ensure permutation is a list
                if not isinstance(permutation, list):
                    permutation = list(range(equiv.width))
                
                circuit_response = CircuitResponse(
                    id=equiv.id,
                    width=equiv.width,
                    length=equiv.gate_count,
                    gates=gates,
                    permutation=permutation,
                    complexity_walk=equiv.complexity_walk,
                    is_representative=False,
                    representative_id=equiv.representative_id
                )
                result.append(circuit_response)
                
            except Exception as e:
                logger.warning(f"Failed to process equivalent circuit {equiv.id}: {e}")
                continue
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API get equivalents failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get equivalents: {str(e)}")

@router.get("/circuits/{circuit_id}/ascii")
async def get_circuit_ascii(
    circuit_id: int,
    factory: IdentityFactory = Depends(get_factory)
) -> CircuitASCIIRepresentation:
    """
    Get ASCII representation of a circuit.
    
    Args:
        circuit_id: Circuit ID
        factory: Factory instance
        
    Returns:
        ASCII diagram of the circuit
    """
    try:
        db = factory.db
        
        # Get circuit
        circuit = db.get_circuit(circuit_id)
        if not circuit:
            raise HTTPException(status_code=404, detail="Circuit not found")
        
        # Generate ASCII representation
        diagram = _generate_ascii_diagram(circuit.gates, circuit.width)
        
        return CircuitASCIIRepresentation(
            circuit_id=circuit_id,
            diagram=diagram
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API get circuit ASCII failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def _generate_ascii_diagram(gates: List[Tuple], width: int) -> str:
    """Generate ASCII diagram for a circuit."""
    lines = []
    
    # Initialize qubit lines
    for i in range(width):
        lines.append(f"q{i}: ───")
    
    # Add gates
    for gate_idx, gate in enumerate(gates):
        try:
            # Handle different gate formats safely
            if isinstance(gate, dict):
                # Skip dictionary gates that can't be visualized
                continue
            elif isinstance(gate, list) and len(gate) == 2:
                controls, target = gate
                # Ensure controls is a list
                if not isinstance(controls, list):
                    continue
            else:
                # Skip malformed gates
                continue
            
            # Add spacing
            for i in range(width):
                lines[i] += "─"
            
            # Add gate symbols
            if len(controls) == 0:  # NOT gate
                lines[target] += "X"
            elif len(controls) == 1:  # CNOT gate
                control = controls[0]
                lines[control] += "●"
                lines[target] += "⊕"
                # Add vertical lines
                start = min(control, target)
                end = max(control, target)
                for i in range(start + 1, end):
                    lines[i] += "│"
            elif len(controls) == 2:  # CCNOT gate
                for control in controls:
                    lines[control] += "●"
                lines[target] += "⊕"
                # Add vertical lines
                all_qubits = sorted(controls + [target])
                for i in range(all_qubits[0] + 1, all_qubits[-1]):
                    if i not in all_qubits:
                        lines[i] += "│"
            
            # Pad other lines
            max_len = max(len(line) for line in lines)
            for i in range(width):
                while len(lines[i]) < max_len:
                    lines[i] += "─"
            
            # Add spacing after gate
            for i in range(width):
                lines[i] += "─"
                
        except Exception as e:
            # Skip problematic gates
            logger.warning(f"Skipping gate {gate_idx} due to error: {e}")
            continue
    
    return "\n".join(lines)



@router.get("/circuits/{circuit_id}/details")
async def get_enhanced_circuit_details(
    circuit_id: int,
    factory: IdentityFactory = Depends(get_factory)
):
    """
    Get enhanced details of a circuit including truth table, Hamming distance plot data,
    and ASCII diagram.
    
    Args:
        circuit_id: Circuit ID
        factory: Factory instance
        
    Returns:
        Enhanced circuit details including truth table and Hamming distance data
    """
    try:
        db = factory.db
        
        # Get circuit
        circuit = db.get_circuit(circuit_id)
        if not circuit:
            raise HTTPException(status_code=404, detail="Circuit not found")
        
        # Generate ASCII representation
        ascii_diagram = _generate_ascii_diagram(circuit.gates, circuit.width)
        
        # Generate truth table by simulating the circuit
        truth_table = _generate_truth_table_from_gates(circuit.gates, circuit.width)
        
        # Get or compute complexity walk (Hamming distances)
        hamming_distances = circuit.complexity_walk if circuit.complexity_walk is not None else []
        
        # Generate gate descriptions
        gate_descriptions = []
        for i, gate in enumerate(circuit.gates):
            if isinstance(gate, list) and len(gate) == 2:
                controls, target = gate
                if isinstance(controls, list):
                    if len(controls) == 0:
                        gate_descriptions.append(f"Gate {i+1}: NOT on qubit {target}")
                    elif len(controls) == 1:
                        gate_descriptions.append(f"Gate {i+1}: CNOT - control: {controls[0]}, target: {target}")
                    elif len(controls) == 2:
                        gate_descriptions.append(f"Gate {i+1}: CCNOT - controls: {controls[0]},{controls[1]}, target: {target}")
                    else:
                        gate_descriptions.append(f"Gate {i+1}: Multi-control gate with {len(controls)} controls")
                else:
                    gate_descriptions.append(f"Gate {i+1}: Invalid controls format")
            else:
                gate_descriptions.append(f"Gate {i+1}: Unknown gate format")
        
        return {
            "circuit_id": circuit_id,
            "width": circuit.width,
            "length": circuit.gate_count,
            "gates": circuit.gates,
            "permutation": circuit.permutation,
            "complexity_walk": circuit.complexity_walk or [],
            "truth_table": truth_table,
            "ascii_diagram": ascii_diagram,
            "hamming_distances": hamming_distances,
            "gate_descriptions": gate_descriptions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API get enhanced circuit details failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

def _generate_truth_table_from_gates(gates: List[Tuple], width: int) -> List[List[int]]:
    """Generate truth table by simulating circuit gates."""
    truth_table = []
    
    for input_value in range(2**width):
        # Convert input to binary representation (LSB first)
        state = [(input_value >> i) & 1 for i in range(width)]
        input_bits = state.copy()
        
        # Simulate each gate
        for gate in gates:
            if isinstance(gate, list) and len(gate) == 2:
                controls, target = gate
                if isinstance(controls, list) and isinstance(target, int):
                    # Check if all control qubits are 1
                    if all(state[c] == 1 for c in controls):
                        # Flip the target qubit
                        state[target] = 1 - state[target]
        
        # Create truth table row: [input_bits] -> [output_bits]
        truth_table.append(input_bits + state)
    
    return truth_table

@router.post("/dim-groups/{dim_group_id}/unroll-all")
async def unroll_all_in_dimension_group(
    dim_group_id: int,
    background_tasks: BackgroundTasks,
    max_equivalents: Optional[int] = Query(100, description="Maximum equivalents per circuit"),
    check_existing: bool = Query(True, description="Check and merge existing sub-seeds"),
    factory: IdentityFactory = Depends(get_factory)
) -> Dict[str, Any]:
    """
    Unroll ALL circuits in a dimension group to generate equivalent circuits.
    This is an exhaustive process that goes through all gate compositions and circuits.
    
    Args:
        dim_group_id: Dimension group ID
        background_tasks: FastAPI background tasks
        max_equivalents: Maximum equivalents per circuit
        check_existing: Check and merge existing sub-seeds
        factory: Factory instance
        
    Returns:
        Batch unrolling result
    """
    try:
        # Check if dimension group exists
        dim_group = factory.db.get_dim_group_by_id(dim_group_id)
        if not dim_group:
            raise HTTPException(status_code=404, detail="Dimension group not found")
        
        # Get all circuits in this dimension group
        all_circuits = factory.db.get_circuits_in_dim_group(dim_group_id)
        
        logger.info(f"API: Starting exhaustive unroll for dimension group {dim_group_id} with {len(all_circuits)} circuits")
        
        # Perform unrolling in background
        def batch_unroll_task():
            import time
            total_processed = 0
            total_equivalents = 0
            total_merged = 0
            start_time = time.time()
            
            for i, circuit in enumerate(all_circuits):
                try:
                    logger.info(f"Batch unroll: Processing circuit {circuit.id} ({i+1}/{len(all_circuits)})")
                    
                    # Perform unroll for this circuit synchronously (no async in background thread)
                    # We'll call the unroller directly instead of the async function
                    unroll_result = factory.unroller.unroll_circuit(circuit, max_equivalents)
                    equivalents = unroll_result.get('equivalents', [])
                    
                    if len(equivalents) > max_equivalents:
                        equivalents = equivalents[:max_equivalents]
                        logger.info(f"Limiting equivalents from {len(equivalents)} to {max_equivalents}")
                    
                    # Store equivalents in database
                    for equiv_gates in equivalents:
                        equiv_id = factory.db.store_equivalent_circuit(
                            original_circuit_id=circuit.id,
                            gates=equiv_gates,
                            width=circuit.width,
                            permutation=circuit.permutation,
                            unroll_type="batch_unroll"
                        )
                    
                    total_processed += 1
                    total_equivalents += len(equivalents)
                    
                    # Update circuit as representative
                    factory.db.update_circuit_as_representative(circuit.id)
                    
                except Exception as e:
                    logger.error(f"Batch unroll failed for circuit {circuit.id}: {e}")
                    continue
            
            end_time = time.time()
            total_time = end_time - start_time
            
            logger.info(f"Batch unroll completed for group {dim_group_id}: "
                       f"{total_processed} circuits processed, "
                       f"{total_equivalents} equivalents generated, "
                       f"{total_merged} sub-seeds merged in {total_time:.2f}s")
        
        background_tasks.add_task(batch_unroll_task)
        
        return {
            "success": True,
            "message": f"Exhaustive unrolling started for dimension group {dim_group_id}",
            "dim_group_id": dim_group_id,
            "total_circuits": len(all_circuits),
            "status": "processing",
            "warning": "This is an exhaustive process that may take significant time to complete"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API batch unroll failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/dim-groups/{dim_group_id}/compositions/{composition}/unroll-all")
async def unroll_all_in_composition(
    dim_group_id: int,
    composition: str,
    background_tasks: BackgroundTasks,
    max_equivalents: Optional[int] = Query(100, description="Maximum equivalents per circuit"),
    check_existing: bool = Query(True, description="Check and merge existing sub-seeds"),
    factory: IdentityFactory = Depends(get_factory)
) -> Dict[str, Any]:
    """
    Unroll ALL circuits in a specific gate composition to generate equivalent circuits.
    
    Args:
        dim_group_id: Dimension group ID
        composition: Gate composition (e.g., "6,0,0")
        background_tasks: FastAPI background tasks
        max_equivalents: Maximum equivalents per circuit
        check_existing: Check and merge existing sub-seeds
        factory: Factory instance
        
    Returns:
        Composition unrolling result
    """
    try:
        # Check if dimension group exists
        dim_group = factory.db.get_dim_group_by_id(dim_group_id)
        if not dim_group:
            raise HTTPException(status_code=404, detail="Dimension group not found")
        
        # Parse composition
        try:
            not_gates, cnot_gates, ccnot_gates = map(int, composition.split(','))
            target_composition = (not_gates, cnot_gates, ccnot_gates)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid composition format")
        
        # Get circuits for this composition
        circuits = factory.db.get_circuits_in_dim_group(dim_group_id)
        composition_circuits = []
        
        for circuit in circuits:
            circuit_composition = _calculate_gate_composition(circuit.gates)
            if circuit_composition == target_composition:
                composition_circuits.append(circuit)
        
        if not composition_circuits:
            raise HTTPException(status_code=404, detail="No circuits found for this composition")
        
        logger.info(f"API: Starting composition unroll for {composition} in group {dim_group_id} with {len(composition_circuits)} circuits")
        
        # Perform unrolling in background
        def composition_unroll_task():
            import time
            total_processed = 0
            total_equivalents = 0
            total_merged = 0
            start_time = time.time()
            
            for i, circuit in enumerate(composition_circuits):
                try:
                    logger.info(f"Composition unroll: Processing circuit {circuit.id} ({i+1}/{len(composition_circuits)})")
                    
                    # Perform unroll for this circuit synchronously (no async in background thread)
                    # We'll call the unroller directly instead of the async function
                    equivalents = factory.unroller.unroll_circuit(circuit.gates, circuit.width)
                    
                    if len(equivalents) > max_equivalents:
                        equivalents = equivalents[:max_equivalents]
                        logger.info(f"Limiting equivalents from {len(equivalents)} to {max_equivalents}")
                    
                    # Store equivalents in database
                    for equiv_gates in equivalents:
                        equiv_id = factory.db.store_equivalent_circuit(
                            original_circuit_id=circuit.id,
                            gates=equiv_gates,
                            width=circuit.width,
                            permutation=circuit.permutation,
                            unroll_type="batch_unroll"
                        )
                    
                    total_processed += 1
                    total_equivalents += len(equivalents)
                    
                    # Update circuit as representative
                    factory.db.update_circuit_as_representative(circuit.id)
                    
                except Exception as e:
                    logger.error(f"Composition unroll failed for circuit {circuit.id}: {e}")
                    continue
            
            end_time = time.time()
            total_time = end_time - start_time
            
            logger.info(f"Composition unroll completed for {composition} in group {dim_group_id}: "
                       f"{total_processed} circuits processed, "
                       f"{total_equivalents} equivalents generated, "
                       f"{total_merged} sub-seeds merged in {total_time:.2f}s")
        
        background_tasks.add_task(composition_unroll_task)
        
        return {
            "success": True,
            "message": f"Composition unrolling started for {composition} in dimension group {dim_group_id}",
            "dim_group_id": dim_group_id,
            "composition": composition,
            "total_circuits": len(composition_circuits),
            "status": "processing",
            "warning": "This process may take significant time depending on the number of circuits"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API composition unroll failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/unroll/{dim_group_id}")
async def unroll_dimension_group(
    dim_group_id: int,
    background_tasks: BackgroundTasks,
    unroll_types: Optional[List[str]] = Query(None, description="Unroll types to apply"),
    factory: IdentityFactory = Depends(get_factory)
) -> Dict[str, Any]:
    """
    Unroll a dimension group to generate equivalent circuits (legacy endpoint).
    
    Args:
        dim_group_id: Dimension group ID
        background_tasks: FastAPI background tasks
        unroll_types: Types of unrolling to apply
        factory: Factory instance
        
    Returns:
        Unrolling result
    """
    try:
        # Check if dimension group exists
        dim_group = factory.db.get_dim_group_by_id(dim_group_id)
        if not dim_group:
            raise HTTPException(status_code=404, detail="Dimension group not found")
        
        # Perform unrolling in background
        def unroll_task():
            result = factory.unroller.unroll_dimension_group(dim_group_id, unroll_types)
            logger.info(f"Background unroll completed for group {dim_group_id}: {result.success}")
        
        background_tasks.add_task(unroll_task)
        
        return {
            "success": True,
            "message": f"Unrolling started for dimension group {dim_group_id}",
            "dim_group_id": dim_group_id,
            "status": "processing"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API unroll failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=FactoryStatsResponse)
async def get_stats(
    factory: IdentityFactory = Depends(get_factory)
) -> FactoryStatsResponse:
    """
    Get factory statistics.
    
    Args:
        factory: Factory instance
        
    Returns:
        Factory statistics
    """
    try:
        stats = factory.get_factory_stats()
        
        return FactoryStatsResponse(
            total_dim_groups=stats.total_dim_groups,
            total_circuits=stats.total_circuits,
            total_seeds_generated=stats.total_representatives,
            total_equivalents_generated=stats.total_equivalents,
            total_simplifications=stats.total_simplifications,
            total_debris_analyses=stats.total_debris_analyses,
            total_ml_analyses=stats.total_ml_analyses,
            active_jobs=stats.active_jobs,
            generation_time=stats.generation_time,
            unroll_time=stats.unroll_time,
            post_process_time=stats.post_process_time,
            debris_analysis_time=stats.debris_analysis_time,
            ml_analysis_time=stats.ml_analysis_time
        )
        
    except Exception as e:
        logger.error(f"API get stats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analyze/{dim_group_id}", response_model=DimGroupAnalysisResponse)
async def analyze_dimension_group(
    dim_group_id: int,
    factory: IdentityFactory = Depends(get_factory)
) -> DimGroupAnalysisResponse:
    """
    Get comprehensive analysis of a dimension group.
    
    Args:
        dim_group_id: Dimension group ID
        factory: Factory instance
        
    Returns:
        Dimension group analysis
    """
    try:
        analysis = factory.get_dimension_group_analysis(dim_group_id)
        
        if 'error' in analysis:
            raise HTTPException(status_code=404, detail=analysis['error'])
        
        return DimGroupAnalysisResponse(
            dim_group_id=analysis['dim_group_id'],
            width=analysis['width'],
            length=analysis['gate_count'],
            total_equivalents=analysis['total_equivalents'],
            is_processed=analysis['is_processed'],
            equivalents=analysis['equivalents']
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API analyze failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/batch-generate", response_model=UnrollResultResponse)
async def batch_generate(
    request: BatchCircuitRequest,
    background_tasks: BackgroundTasks,
    factory: IdentityFactory = Depends(get_factory)
) -> UnrollResultResponse:
    """
    Generate multiple identity circuits in batch.
    
    Args:
        request: Batch generation parameters
        background_tasks: FastAPI background tasks
        factory: Factory instance
        
    Returns:
        Batch generation result
    """
    try:
        logger.info(f"API: Batch generating {len(request.dimensions)} circuits")
        
        # Convert dimensions
        dimensions = [(d.width, d.gate_count) for d in request.dimensions]
        
        if request.use_background:
            # Process in background
            def batch_task():
                results = factory.batch_generate(
                    dimensions,
                    use_job_queue=request.use_job_queue,
                    max_inverse_gates=request.max_inverse_gates
                )
                logger.info(f"Background batch completed: {len(results)} results")
            
            background_tasks.add_task(batch_task)
            
            return UnrollResultResponse(
                success=True,
                dim_group_id=0,  # placeholder for batch
                total_equivalents=0,
                new_circuits=len(dimensions)
            )
        else:
            # Process synchronously
            results = factory.batch_generate(
                dimensions,
                use_job_queue=request.use_job_queue,
                max_inverse_gates=request.max_inverse_gates
            )
            
            successful = sum(1 for r in results.values() if r['success'])
            
            return UnrollResultResponse(
                success=True,
                dim_group_id=0,  # placeholder for batch
                total_equivalents=sum(r.get('total_equivalents', 0) for r in results.values() if r['success']),
                new_circuits=successful
            )
        
    except Exception as e:
        logger.error(f"API batch generate failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/dimension-groups/{dim_group_id}")
async def delete_dimension_group(
    dim_group_id: int,
    factory: IdentityFactory = Depends(get_factory)
) -> Dict[str, Any]:
    """
    Delete a dimension group and all associated circuits.
    
    Args:
        dim_group_id: Dimension group ID
        factory: Factory instance
        
    Returns:
        Deletion result
    """
    try:
        # Check if dimension group exists
        dim_group = factory.db.get_dim_group_by_id(dim_group_id)
        if not dim_group:
            raise HTTPException(status_code=404, detail="Dimension group not found")
        
        # Delete dimension group (this should cascade to delete associated circuits)
        success = factory.db.delete_dim_group(dim_group_id)
        
        if success:
            return {
                "success": True,
                "message": f"Dimension group {dim_group_id} deleted successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete dimension group")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API delete dimension group failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Health check endpoint
@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "identity-circuit-factory"}

# Version endpoint
@router.get("/version")
async def get_version() -> Dict[str, str]:
    """Get API version information."""
    return {
        "version": "1.0.0",
        "api_version": "v1",
        "service": "identity-circuit-factory"
    }

@router.post("/dim-groups/{dim_group_id}/cleanup")
async def cleanup_dimension_group(
    dim_group_id: int,
    factory: IdentityFactory = Depends(get_factory)
) -> Dict[str, Any]:
    """
    Clean up duplicate representatives and reorganize sub-seeds in a dimension group.
    
    Args:
        dim_group_id: Dimension group ID to clean up
        factory: Factory instance
        
    Returns:
        Cleanup results
    """
    try:
        db = factory.db
        
        # Check if dimension group exists
        dim_group = db.get_dim_group_by_id(dim_group_id)
        if not dim_group:
            raise HTTPException(status_code=404, detail="Dimension group not found")
        
        logger.info(f"Starting cleanup for dimension group {dim_group_id}")
        
        # Clean up duplicate representatives
        duplicates_cleaned = db.cleanup_duplicate_representatives(dim_group_id)
        
        logger.info(f"Cleanup completed for dimension group {dim_group_id}: {duplicates_cleaned} duplicates cleaned")
        
        return {
            "success": True,
            "dim_group_id": dim_group_id,
            "duplicates_cleaned": duplicates_cleaned,
            "message": f"Cleaned up {duplicates_cleaned} duplicate representatives"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cleanup failed for dimension group {dim_group_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 