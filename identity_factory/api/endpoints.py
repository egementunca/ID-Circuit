"""
API endpoints for the Identity Circuit Factory.
Provides REST API for generating, retrieving, and managing identity circuits.
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from fastapi.responses import JSONResponse
import asyncio

from .models import (
    CircuitRequest, GenerationResultResponse, 
    DimGroupResponse, CircuitResponse,
    FactoryStatsResponse, DimGroupAnalysisResponse,
    BatchCircuitRequest, UnrollResultResponse
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
router = APIRouter(prefix="/api/v1", tags=["identity-circuits"])

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
            max_inverse_gates=request.max_inverse_gates,
            solver=request.solver
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
        
        # Get equivalents count
        equivalents_count = 0
        if 'unrolling' in result and isinstance(result['unrolling'], dict):
            equivalents_count = result['unrolling'].get('total_equivalents', 0)
        
        return GenerationResultResponse(
            success=True,
            circuit_id=circuit_id,
            dim_group_id=dim_group_id,
            representative_id=representative_id,
            width=request.width,
            gate_count=request.gate_count,
            total_equivalents=equivalents_count,
            generation_time=result.get('total_time', 0.0),
            processing_steps=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dimension-groups", response_model=List[DimGroupResponse])
async def list_dimension_groups(
    width: Optional[int] = Query(None, description="Filter by width"),
    gate_count: Optional[int] = Query(None, description="Filter by gate count"),
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
        if width and gate_count:
            dim_group = db.get_dim_group_by_dimensions(width, gate_count)
            dim_groups = [dim_group] if dim_group else []
        elif width:
            dim_groups = db.get_dim_groups_by_width(width)
        else:
            dim_groups = db.get_all_dim_groups()
        
        # Filter processed if requested
        if processed_only:
            dim_groups = [dg for dg in dim_groups if dg.is_processed]
        
        # Convert to response format
        responses = []
        for dg in dim_groups:
            # Get representatives
            representatives = db.get_representatives_for_dim_group(dg.id)
            
            # Get equivalents count
            equivalents = db.get_all_equivalents_for_dim_group(dg.id)
            
            responses.append(DimGroupResponse(
                id=dg.id,
                width=dg.width,
                gate_count=dg.gate_count,
                circuit_count=dg.circuit_count,
                is_processed=dg.is_processed,
                representatives=[
                    {
                        'id': rep.id,
                        'circuit_id': rep.circuit_id,
                        'gate_composition': rep.gate_composition,
                        'is_primary': rep.is_primary
                    }
                    for rep in representatives
                ],
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
            gate_count=dim_group.gate_count,
            circuit_count=dim_group.circuit_count,
            is_processed=dim_group.is_processed,
            representatives=[
                {
                    'id': rep.id,
                    'circuit_id': rep.circuit_id,
                    'gate_composition': rep.gate_composition,
                    'is_primary': rep.is_primary
                }
                for rep in representatives
            ],
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
            gate_count=circuit.gate_count,
            gates=circuit.gates,
            permutation=circuit.permutation
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"API get circuit failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/unroll/{dim_group_id}")
async def unroll_dimension_group(
    dim_group_id: int,
    background_tasks: BackgroundTasks,
    unroll_types: Optional[List[str]] = Query(None, description="Unroll types to apply"),
    factory: IdentityFactory = Depends(get_factory)
) -> Dict[str, Any]:
    """
    Unroll a dimension group to generate equivalent circuits.
    
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
        
        return StatsResponse(
            total_dim_groups=stats.total_dim_groups,
            total_circuits=stats.total_circuits,
            total_representatives=stats.total_representatives,
            total_equivalents=stats.total_equivalents,
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
        
        return AnalysisResponse(
            dim_group_id=analysis['dim_group_id'],
            width=analysis['width'],
            gate_count=analysis['gate_count'],
            circuit_count=analysis['circuit_count'],
            total_equivalents=analysis['total_equivalents'],
            is_processed=analysis['is_processed'],
            representatives=analysis['representatives'],
            equivalents_by_unroll_type=analysis['equivalents']['by_unroll_type'],
            gate_composition_analysis=analysis['equivalents']['by_gate_composition']
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
                    max_inverse_gates=request.max_inverse_gates,
                    solver=request.solver
                )
                logger.info(f"Background batch completed: {len(results)} results")
            
            background_tasks.add_task(batch_task)
            
            return BatchGenerateResponse(
                success=True,
                total_requested=len(dimensions),
                results={},
                status="processing",
                message=f"Batch generation started for {len(dimensions)} circuits"
            )
        else:
            # Process synchronously
            results = factory.batch_generate(
                dimensions,
                use_job_queue=request.use_job_queue,
                max_inverse_gates=request.max_inverse_gates,
                solver=request.solver
            )
            
            successful = sum(1 for r in results.values() if r['success'])
            
            return BatchGenerateResponse(
                success=True,
                total_requested=len(dimensions),
                total_successful=successful,
                results=results,
                status="completed"
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