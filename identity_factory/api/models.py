"""
Pydantic models for API request/response schemas.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Tuple
from datetime import datetime
from enum import Enum

class UnrollType(str, Enum):
    """Types of unrolling operations."""
    SWAP = "swap"
    ROTATION = "rotation"
    PERMUTATION = "permutation"
    REVERSE = "reverse"
    LOCAL_UNROLL = "local_unroll"
    FULL_UNROLL = "full_unroll"

class SimplificationType(str, Enum):
    """Types of simplification operations."""
    SWAP_CANCEL = "swap_cancel"
    TEMPLATE = "template"
    NONE = "none"

class JobType(str, Enum):
    """Types of jobs that can be processed."""
    SEED_GENERATION = "seed_generation"
    UNROLLING = "unrolling"
    POST_PROCESSING = "post_processing"
    DEBRIS_ANALYSIS = "debris_analysis"
    ML_FEATURE_EXTRACTION = "ml_feature_extraction"
    PARQUET_EXPORT = "parquet_export"

class JobStatus(str, Enum):
    """Job status values."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class CircuitRequest(BaseModel):
    """Request model for circuit generation."""
    width: int = Field(..., ge=1, le=10, description="Number of qubits")
    length: int = Field(..., ge=1, le=50, description="Number of gates in forward circuit")
    max_inverse_gates: Optional[int] = Field(40, ge=1, le=100, description="Maximum inverse gates")
    sequential: Optional[bool] = Field(True, description="Use sequential gate generation")
    enable_unrolling: Optional[bool] = Field(True, description="Enable unrolling step")
    enable_post_processing: Optional[bool] = Field(True, description="Enable post-processing step")
    enable_debris_analysis: Optional[bool] = Field(True, description="Enable debris cancellation analysis")
    enable_ml_analysis: Optional[bool] = Field(True, description="Enable ML feature extraction")
    use_job_queue: Optional[bool] = Field(False, description="Use distributed processing")

class BatchCircuitRequest(BaseModel):
    """Request model for batch circuit generation."""
    dimensions: List[Tuple[int, int]] = Field(..., description="List of (width, length) tuples")
    max_inverse_gates: Optional[int] = Field(40, ge=1, le=100)
    sequential: Optional[bool] = Field(True)
    enable_unrolling: Optional[bool] = Field(True)
    enable_post_processing: Optional[bool] = Field(True)
    enable_debris_analysis: Optional[bool] = Field(True)
    enable_ml_analysis: Optional[bool] = Field(True)
    use_job_queue: Optional[bool] = Field(False)

class UnrollRequest(BaseModel):
    """Request model for unrolling operations."""
    dim_group_id: int = Field(..., description="Dimension group ID to unroll")
    unroll_types: Optional[List[UnrollType]] = Field(None, description="Types of unrolling to apply")
    max_equivalents: Optional[int] = Field(10000, ge=1, le=100000, description="Maximum equivalent circuits")

class SimplificationRequest(BaseModel):
    """Request model for simplification operations."""
    dim_group_id: int = Field(..., description="Dimension group ID to simplify")
    simplification_types: Optional[List[SimplificationType]] = Field(None, description="Types of simplification to apply")

class DebrisAnalysisRequest(BaseModel):
    """Request model for debris cancellation analysis."""
    dim_group_id: int = Field(..., description="Dimension group ID")
    circuit_id: int = Field(..., description="Circuit ID to analyze")
    max_debris_gates: Optional[int] = Field(5, ge=1, le=10, description="Maximum debris gates to insert")

class MLAnalysisRequest(BaseModel):
    """Request model for ML feature analysis."""
    circuit_id: int = Field(..., description="Circuit ID to analyze")
    dim_group_id: int = Field(..., description="Dimension group ID")

class ExportRequest(BaseModel):
    """Request model for export operations."""
    dim_group_id: int = Field(..., description="Dimension group ID to export")
    output_path: str = Field(..., description="Output file path")

class ImportRequest(BaseModel):
    """Request model for import operations."""
    import_path: str = Field(..., description="Path to import file")
    overwrite_existing: Optional[bool] = Field(False, description="Overwrite existing dimension groups")

class RecommendationRequest(BaseModel):
    """Request model for dimension recommendations."""
    target_width: int = Field(..., ge=1, le=10, description="Target number of qubits")
    max_length: Optional[int] = Field(20, ge=1, le=50, description="Maximum circuit length")
    limit: Optional[int] = Field(10, ge=1, le=100, description="Number of recommendations")

class CircuitResponse(BaseModel):
    """Response model for circuit data."""
    id: int
    width: int
    length: int
    gates: List[Tuple]
    permutation: List[int]
    complexity_walk: Optional[List[int]] = None
    circuit_hash: Optional[str] = None

class DimGroupResponse(BaseModel):
    """Response model for dimension group data."""
    id: int
    width: int
    length: int
    seed_circuit_id: Optional[int]
    representative_circuit_id: Optional[int]
    total_equivalents: int
    is_processed: bool

class RepresentativeCircuitResponse(BaseModel):
    """Response model for a representative circuit within a dimension group."""
    circuit: CircuitResponse
    gate_composition: Tuple[int, int, int]
    composition_count: int

class CircuitASCIIRepresentation(BaseModel):
    """Response model for a circuit's ASCII diagram."""
    circuit_id: int
    diagram: str

class CircuitEquivalentResponse(BaseModel):
    """Response model for circuit equivalent data."""
    id: int
    circuit_id: int
    dim_group_id: int
    parent_seed_id: Optional[int]
    unroll_type: Optional[str]
    unroll_params: Optional[Dict[str, Any]]
    gate_composition: Optional[Tuple[int, int, int]]

class SimplificationResponse(BaseModel):
    """Response model for simplification data."""
    id: int
    original_circuit_id: int
    simplified_circuit_id: Optional[int]
    target_dim_group_id: Optional[int]
    reduction_metrics: Optional[Dict[str, Any]]
    simplification_type: str

class GenerationResultResponse(BaseModel):
    """Response model for generation results."""
    success: bool
    width: int
    length: int
    seed_circuit_id: Optional[int] = None
    dim_group_id: Optional[int] = None
    total_equivalents: Optional[int] = None
    successful_simplifications: Optional[int] = None
    total_time: float
    error_message: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None
    debris_analysis: Optional[Dict[str, Any]] = None
    ml_analysis: Optional[Dict[str, Any]] = None

class UnrollResultResponse(BaseModel):
    """Response model for unrolling results."""
    success: bool
    dim_group_id: int
    total_equivalents: int
    new_circuits: int
    unroll_types: Optional[Dict[str, int]] = None
    error_message: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None

class SimplificationResultResponse(BaseModel):
    """Response model for simplification results."""
    success: bool
    original_circuit_id: int
    simplified_circuit_id: Optional[int] = None
    target_dim_group_id: Optional[int] = None
    reduction_metrics: Optional[Dict[str, Any]] = None
    simplification_type: str
    error_message: Optional[str] = None

class JobResponse(BaseModel):
    """Response model for job data."""
    id: int
    job_type: str
    status: str
    priority: int
    parameters: Dict[str, Any]
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    created_at: Optional[datetime] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @classmethod
    def from_job_record(cls, job_record):
        """Create JobResponse from JobRecord."""
        return cls(
            id=job_record.id,
            job_type=job_record.job_type,
            status=job_record.status,
            priority=job_record.priority,
            parameters=job_record.parameters,
            result=job_record.result,
            error_message=job_record.error_message,
            created_at=job_record.created_at,
            started_at=job_record.started_at,
            completed_at=job_record.completed_at
        )

class DebrisAnalysisResponse(BaseModel):
    """Response model for debris cancellation analysis."""
    improvement_found: bool
    original_gate_count: Optional[int] = None
    final_gate_count: Optional[int] = None
    non_triviality_score: Optional[float] = None
    debris_gates: List[Tuple] = []
    cancellation_path: List[int] = []

class MLAnalysisResponse(BaseModel):
    """Response model for ML feature analysis."""
    circuit_id: int
    dim_group_id: int
    features: Dict[str, float]
    complexity_prediction: float
    optimization_suggestions: List[str]
    feature_summary: Optional[Dict[str, Any]] = None

class MLStatisticsResponse(BaseModel):
    """Response model for ML statistics."""
    dim_group_id: int
    avg_complexity: float
    complexity_distribution: List[float]
    common_optimizations: List[str]
    feature_correlations: Dict[str, float]

class DimGroupAnalysisResponse(BaseModel):
    """Response model for comprehensive dimension group analysis."""
    dim_group_id: int
    width: int
    length: int
    total_equivalents: int
    is_processed: bool
    equivalents: Dict[str, Any]
    debris_analysis: Optional[Dict[str, Any]] = None
    ml_analysis: Optional[Dict[str, Any]] = None

class FactoryStatsResponse(BaseModel):
    """Response model for factory statistics."""
    total_dim_groups: int
    total_circuits: int
    total_seeds_generated: int
    total_equivalents_generated: int
    total_simplifications: int
    total_debris_analyses: int = 0
    total_ml_analyses: int = 0
    active_jobs: int = 0
    generation_time: float = 0.0
    unroll_time: float = 0.0
    post_process_time: float = 0.0
    debris_analysis_time: float = 0.0
    ml_analysis_time: float = 0.0

class DetailedStatsResponse(BaseModel):
    """Response model for detailed statistics."""
    factory_stats: FactoryStatsResponse
    seed_stats: Dict[str, Any]
    unroll_stats: Dict[str, Any]
    post_stats: Dict[str, Any]
    job_stats: Optional[Dict[str, Any]] = None

class PaginationParams(BaseModel):
    """Pagination parameters."""
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(50, ge=1, le=1000, description="Page size")
    sort_by: Optional[str] = Field(None, description="Sort field")
    sort_order: Optional[str] = Field("asc", pattern="^(asc|desc)$", description="Sort order")

class PaginatedResponse(BaseModel):
    """Generic paginated response."""
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int

class SearchParams(BaseModel):
    """Search parameters."""
    width: Optional[int] = Field(None, ge=1, le=10, description="Filter by width")
    length: Optional[int] = Field(None, ge=1, le=50, description="Filter by length")
    min_equivalents: Optional[int] = Field(None, ge=0, description="Minimum equivalents")
    max_equivalents: Optional[int] = Field(None, ge=0, description="Maximum equivalents")
    gate_type: Optional[str] = Field(None, pattern="^(NOT|CNOT|TOFFOLI)$", description="Filter by gate type")

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime
    version: str
    database_connected: bool
    sat_solver_available: bool
    job_queue_running: bool = False

class ErrorResponse(BaseModel):
    """Error response model."""
    error: str
    detail: Optional[str] = None
    timestamp: datetime
    request_id: Optional[str] = None 