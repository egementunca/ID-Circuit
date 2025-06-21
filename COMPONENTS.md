# Identity Factory Components Documentation

This document provides detailed explanations of each component in the Identity Circuit Factory system.

## 🏗️ System Architecture Overview

The Identity Factory is built as a modular system with clear separation of concerns:

```
Identity Factory
├── Core Engine (factory_manager.py)
├── Data Layer (database.py)
├── Circuit Generation (seed_generator.py)
├── Transformation Layer (unroller.py)
├── Optimization Layer (post_processor.py)
├── Analysis Layer (debris_cancellation.py, ml_features.py)
├── API Layer (api/)
├── CLI Interface (cli.py)
└── Job System (job_queue.py)
```

---

## 🔧 Core Components

### 1. Factory Manager (`factory_manager.py`)

**Purpose**: The central orchestrator that coordinates all operations in the Identity Factory.

**Key Responsibilities**:

-   Manages the entire circuit generation pipeline
-   Coordinates between different components
-   Handles configuration and initialization
-   Provides high-level API for external users

**Main Classes**:

-   `FactoryConfig`: Configuration dataclass for factory settings
-   `IdentityFactory`: Main factory class that orchestrates everything

**Key Methods**:

```python
# Generate a single identity circuit
factory.generate_identity_circuit(width=3, gate_count=5)

# Generate multiple circuits in batch
factory.batch_generate([(3,3), (3,4), (4,3)])

# Get factory statistics
stats = factory.get_factory_stats()

# Analyze a dimension group
analysis = factory.get_dimension_group_analysis(dim_group_id)
```

**Configuration Options**:

-   `db_path`: Database file location
-   `max_inverse_gates`: Maximum gates for inverse synthesis
-   `enable_post_processing`: Whether to run simplification
-   `enable_ml_features`: Whether to extract ML features
-   `solver`: Which SAT solver to use

### 2. Database Manager (`database.py`)

**Purpose**: Manages all data persistence using SQLite database with the corrected schema.

**Key Responsibilities**:

-   Stores circuit data and metadata
-   Manages dimension groups as collections of identity circuits
-   Tracks representatives chosen from dimension groups
-   Handles relationships between circuits and equivalents

**Main Tables**:

-   `circuits`: Individual circuit data
-   `dim_groups`: Collections of circuits with same (width, gate_count)
-   `representatives`: Representative circuits chosen from dimension groups
-   `circuit_equivalents`: Equivalent circuits generated from representatives
-   `simplifications`: Circuit simplification records
-   `debris_cancellation_records`: Debris analysis results
-   `ml_features`: Machine learning features
-   `jobs`: Background job tracking

**Key Data Classes**:

```python
@dataclass
class DimGroupRecord:
    """Represents a dimension group - collection of identity circuits."""
    id: Optional[int]
    width: int
    gate_count: int
    circuit_count: int
    is_processed: bool

@dataclass
class RepresentativeRecord:
    """Represents a representative circuit chosen from a dimension group."""
    id: Optional[int]
    dim_group_id: int
    circuit_id: int
    gate_composition: Dict[str, int]
    is_primary: bool
```

**Key Methods**:

```python
# Store a new circuit in a dimension group
db.store_circuit(circuit_record)

# Get representatives for a dimension group
representatives = db.get_representatives_for_dim_group(dim_group_id)

# Get all equivalents for a dimension group
equivalents = db.get_all_equivalents_for_dim_group(dim_group_id)
```

---

## 🔬 Circuit Generation & Management

### 3. Seed Generator (`seed_generator.py`)

**Purpose**: Creates identity circuits and manages representative selection.

**How It Works**:

1. Generates identity circuits using SAT-based synthesis
2. Organizes circuits into dimension groups by (width, gate_count)
3. Optionally selects representatives from generated circuits
4. Validates circuits are truly identity circuits

**Key Classes**:

-   `SeedGenerator`: Main generator class
-   `SeedGenerationResult`: Result container

**Key Methods**:

```python
# Generate a single identity circuit
result = generator.generate_seed(width=3, gate_count=5)

# Generate with representative selection
result = generator.generate_seed(width=3, gate_count=5, create_representative=True)
```

**Algorithm**:

1. **Random Permutation**: Creates a random permutation of qubits
2. **SAT Synthesis**: Uses `sat_revsynth` to find inverse circuit
3. **Validation**: Ensures the combined circuit is identity
4. **Dimension Grouping**: Places circuit in appropriate dimension group
5. **Representative Selection**: Optionally marks circuit as representative

### 4. Circuit Unroller (`unroller.py`)

**Purpose**: Creates equivalent circuits from representative circuits through transformations.

**Transformation Types**:

-   **Swap Operations**: Swaps adjacent gates that commute
-   **Rotations**: Rotates the entire circuit
-   **Permutations**: Applies qubit permutations
-   **Reversals**: Reverses gate order
-   **Local Unroll**: Explores local transformations
-   **Full Unroll**: Comprehensive exploration using sat_revsynth

**Key Classes**:

-   `CircuitUnroller`: Main unroller class
-   `UnrollResult`: Result container

**Key Methods**:

```python
# Unroll all representatives in a dimension group
result = unroller.unroll_dimension_group(dim_group_id)

# Unroll with specific transformation types
result = unroller.unroll_dimension_group(
    dim_group_id,
    unroll_types=['swap', 'rotation']
)

# Unroll all unprocessed dimension groups
results = unroller.unroll_all_dimension_groups()
```

**Algorithm**:

1. **Load Representatives**: Gets all representative circuits from dimension group
2. **Apply Transformations**: Uses `sat_revsynth` circuit operations on each representative
3. **Generate Equivalents**: Creates new circuits through transformations
4. **Deduplication**: Removes duplicate circuits (handled by database constraints)
5. **Storage**: Saves equivalent circuits with relationships to representatives

---

## ⚡ Optimization & Analysis

### 5. Post Processor (`post_processor.py`)

**Purpose**: Simplifies and optimizes circuits using various techniques.

**Simplification Types**:

-   **Swap Cancellation**: Cancels adjacent swap gates
-   **Template Matching**: Applies known simplification patterns
-   **Gate Cancellation**: Removes redundant gates

**Key Classes**:

-   `PostProcessor`: Main processor class
-   `SimplificationResult`: Result container

**Key Methods**:

```python
# Simplify a single circuit
result = processor.simplify_circuit(circuit_id)

# Simplify entire dimension group
results = processor.simplify_dimension_group(dim_group_id)
```

### 6. Debris Cancellation (`debris_cancellation.py`)

**Purpose**: Analyzes circuits for debris cancellation opportunities and non-triviality.

**Key Features**:

-   Identifies potential debris gates
-   Calculates non-triviality scores
-   Suggests optimizations

**Key Methods**:

```python
# Analyze a representative circuit
result = debris_manager.analyze_dim_group_representative(dim_group_id, circuit_id)

# Get high-complexity circuits
circuits = debris_manager.get_high_complexity_circuits(threshold=2.0)
```

### 7. ML Features (`ml_features.py`)

**Purpose**: Extracts machine learning features from circuits for analysis and optimization.

**Feature Types**:

-   Gate composition features
-   Circuit complexity metrics
-   Structural features
-   Optimization potential indicators

**Key Methods**:

```python
# Extract features from a circuit
features = ml_manager.extract_features(circuit)

# Analyze circuit with ML
result = ml_manager.analyze_circuit(circuit_id, dim_group_id, circuit)
```

---

## 🌐 API Layer

### 8. API Server (`api/server.py`)

**Purpose**: Provides REST API interface for the Identity Factory.

**Key Features**:

-   FastAPI-based REST API
-   Automatic OpenAPI documentation
-   Background task processing
-   Error handling and validation

### 9. API Endpoints (`api/endpoints.py`)

**Main Endpoints**:

-   `POST /api/v1/generate` - Generate identity circuits
-   `GET /api/v1/dimension-groups` - List dimension groups
-   `GET /api/v1/dimension-groups/{id}` - Get dimension group details
-   `POST /api/v1/unroll/{id}` - Unroll dimension group
-   `GET /api/v1/analyze/{id}` - Analyze dimension group
-   `POST /api/v1/batch-generate` - Batch generate circuits

### 10. API Models (`api/models.py`)

**Key Models**:

```python
class GenerateRequest(BaseModel):
    width: int
    gate_count: int
    enable_unrolling: bool = True
    enable_post_processing: bool = True

class DimensionGroupResponse(BaseModel):
    id: int
    width: int
    gate_count: int
    circuit_count: int
    representatives: List[Dict[str, Any]]
    total_equivalents: int
```

---

## 🖥️ User Interfaces

### 11. CLI Interface (`cli.py`)

**Purpose**: Command-line interface for direct usage.

**Main Commands**:

```bash
# Generate identity circuit
python -m identity_factory generate 3 5

# List dimension groups with representatives
python -m identity_factory list --show-representatives

# Unroll dimension group
python -m identity_factory unroll 1

# Analyze dimension group
python -m identity_factory analyze 1

# Get statistics
python -m identity_factory stats
```

### 12. Job Queue (`job_queue.py`)

**Purpose**: Background job processing for long-running operations.

**Features**:

-   Redis-based job queue
-   Distributed processing
-   Job status tracking
-   Error handling and retry logic

---

## 📊 Data Flow

### Circuit Generation Flow

1. **Request**: User requests identity circuit generation
2. **Generation**: `SeedGenerator` creates identity circuit
3. **Grouping**: Circuit is placed in appropriate dimension group
4. **Representative**: Circuit may be marked as representative
5. **Unrolling**: Representatives generate equivalent circuits
6. **Storage**: All circuits and relationships are stored

### Analysis Flow

1. **Selection**: User selects dimension group for analysis
2. **Retrieval**: System retrieves all circuits and representatives
3. **Processing**: Various analyses are performed (ML, debris, etc.)
4. **Aggregation**: Results are aggregated and summarized
5. **Response**: Analysis results are returned to user

---

## 🔧 Configuration & Customization

### Factory Configuration

```python
config = FactoryConfig(
    db_path="circuits.db",
    max_inverse_gates=40,
    max_equivalents=10000,
    solver="minisat-gh",
    enable_unrolling=True,
    enable_post_processing=True,
    enable_debris_analysis=True,
    enable_ml_features=True
)
```

### Component Customization

Each component can be configured independently:

-   **SeedGenerator**: SAT solver, maximum attempts, validation settings
-   **Unroller**: Transformation types, maximum equivalents, deduplication
-   **PostProcessor**: Simplification techniques, optimization levels
-   **Database**: Connection settings, schema options

---

## 🚀 Performance Considerations

### Scalability

-   **Database**: SQLite with proper indexing for fast queries
-   **Memory**: Efficient circuit representation and caching
-   **Processing**: Background jobs for long-running operations
-   **API**: Async endpoints with proper resource management

### Optimization

-   **Caching**: Frequently accessed data is cached
-   **Batching**: Multiple operations are batched when possible
-   **Indexing**: Database indexes on frequently queried columns
-   **Lazy Loading**: Data is loaded only when needed
