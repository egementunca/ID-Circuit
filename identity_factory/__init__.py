"""
Identity Circuit Factory.

A fully automatic identity circuit generation factory built on the sat_revsynth library.
Supports seed generation, circuit unrolling, post-processing, debris cancellation analysis,
ML feature extraction, and distributed processing via job queue.
"""

from .factory_manager import IdentityFactory, FactoryConfig, FactoryStats
from .database import (
    CircuitDatabase, 
    CircuitRecord, 
    DimGroupRecord, 
    JobRecord,
)
from .seed_generator import SeedGenerator, SeedGenerationResult
from .unroller import CircuitUnroller, UnrollResult
from .post_processor import PostProcessor, SimplificationResult
from .debris_cancellation import (
    DebrisCancellationManager, 
    DebrisCancellationAnalyzer,
    CancellationPath,
    DebrisInsertion
)
from .job_queue import (
    JobQueueManager, 
    AsyncJobQueueManager, 
    JobType, 
    JobStatus, 
    JobProcessor
)
from .ml_features import (
    MLFeatureManager,
    MLFeatureExtractor,
    ComplexityPredictor,
    OptimizationAdvisor,
    CircuitFeatures
)

__version__ = "2.0.0"
__author__ = "Identity Circuit Factory Team"

__all__ = [
    # Core factory components
    "IdentityFactory",
    "FactoryConfig", 
    "FactoryStats",
    
    # Database
    "CircuitDatabase",
    "CircuitRecord",
    "DimGroupRecord", 
    "JobRecord",
    
    # Core processing components
    "SeedGenerator",
    "SeedGenerationResult",
    "CircuitUnroller", 
    "UnrollResult",
    "PostProcessor",
    "SimplificationResult",
    
    # Debris cancellation system
    "DebrisCancellationManager",
    "DebrisCancellationAnalyzer",
    "CancellationPath",
    "DebrisInsertion",
    
    # Job queue system
    "JobQueueManager",
    "AsyncJobQueueManager", 
    "JobType",
    "JobStatus",
    "JobProcessor",
    
    # ML features system
    "MLFeatureManager",
    "MLFeatureExtractor",
    "ComplexityPredictor",
    "OptimizationAdvisor",
    "CircuitFeatures",
] 