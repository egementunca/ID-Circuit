# ID-Circuit: Technical Component Documentation

This document provides detailed technical information about the ID-Circuit system architecture, component interactions, and implementation details.

## System Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Web Frontend  │    │   REST API      │    │   Core Engine   │
│   (frontend.html)│◄──►│   (FastAPI)     │◄──►│   (Factory)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
                                ▼                       ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │   Database      │    │   SAT Synthesis │
                       │   (SQLite)      │    │   (sat_revsynth)│
                       └─────────────────┘    └─────────────────┘
```

## Core Components

### 1. Factory Manager (`identity_factory/factory_manager.py`)

**Purpose**: Main orchestrator that coordinates all system operations.

**Key Responsibilities**:

-   Initialize and manage all system components
-   Coordinate circuit generation workflow
-   Handle configuration and logging setup
-   Manage job queue for background processing

**Key Classes**:

-   `IdentityFactory`: Main factory class
-   `FactoryConfig`: Configuration management
-   `FactoryStats`: Statistics tracking

**Data Flow**:

```
User Request → Factory Manager → Component Orchestration → Database Storage
```

### 2. Seed Generator (`identity_factory/seed_generator.py`)

**Purpose**: Generate identity circuits using SAT-based synthesis.

**Key Responsibilities**:

-   Create forward and inverse circuits
-   Combine circuits to form identity circuits
-   Manage circuit deduplication
-   Handle representative selection

**Key Classes**:

-   `SeedGenerator`: Main generation engine
-   `SeedGenerationResult`: Generation results

**Algorithm**:

1. Generate random forward circuit using SAT synthesis
2. Compute inverse circuit
3. Combine forward + inverse = identity circuit
4. Check for duplicates and manage representatives

### 3. Circuit Unroller (`identity_factory/unroller.py`)

**Purpose**: Generate equivalent circuits from representatives using transformations.

**Key Responsibilities**:

-   Apply sat_revsynth unrolling algorithms
-   Store equivalent circuits in database
-   Manage unrolling statistics
-   Handle data validation and error recovery

**Key Classes**:

-   `CircuitUnroller`: Main unrolling engine
-   `UnrollResult`: Unrolling operation results

**Transformation Methods**:

-   `circuit.unroll([])`: Full sat_revsynth unrolling
-   Swap space exploration
-   Circuit rotations and permutations
-   Reverse operations

**Data Flow**:

```
Representative Circuit → sat_revsynth.unroll() → Equivalent Circuits → Database Storage
```

### 4. Database Layer (`identity_factory/database.py`)

**Purpose**: SQLite-based persistence with relationship management.

**Key Responsibilities**:

-   Store and retrieve circuit data
-   Manage dimension group relationships
-   Handle representative and equivalent mappings
-   Provide efficient querying capabilities

**Key Classes**:

-   `CircuitDatabase`: Main database manager
-   `CircuitRecord`: Circuit data structure
-   `DimGroupRecord`: Dimension group data
-   `RepresentativeRecord`: Representative mappings

**Database Schema**:

```sql
-- Core tables
circuits (id, width, gate_count, gates, permutation, representative_id, ...)
dim_groups (id, width, gate_count, circuit_count, is_processed, ...)
representatives (id, dim_group_id, circuit_id, gate_composition, ...)
equivalents (id, circuit_id, representative_id, unroll_type, ...)
dim_group_circuits (dim_group_id, circuit_id) -- Many-to-many relationship
```

**Key Relationships**:

-   Circuits belong to dimension groups (many-to-many)
-   Representatives are selected from circuits
-   Equivalents point to their representative circuits
-   All circuits have a `representative_id` (self-reference for representatives)

### 5. API Layer (`identity_factory/api/`)

**Purpose**: FastAPI-based REST API for external access.

**Key Components**:

-   `server.py`: FastAPI application setup
-   `endpoints.py`: API endpoint definitions
-   `models.py`: Pydantic request/response models
-   `client.py`: Python client library

**Key Endpoints**:

```
POST /api/v1/generate          # Generate new circuits
GET  /api/v1/dim-groups        # List dimension groups
GET  /api/v1/dim-groups/{id}/representatives  # Get representatives
POST /api/v1/circuits/{id}/unroll             # Unroll a circuit
GET  /api/v1/circuits/{id}/equivalents        # Get equivalents
GET  /api/v1/circuits/{id}/ascii              # Get ASCII diagram
POST /api/v1/dim-groups/{id}/unroll-all       # Unroll all representatives
```

### 6. Web Interface (`frontend.html`)

**Purpose**: Modern JavaScript-based user interface.

**Key Features**:

-   Real-time circuit visualization
-   Interactive dimension group management
-   Circuit unrolling controls
-   ASCII diagram display
-   Statistics dashboard

**Technologies**:

-   Vanilla JavaScript (no frameworks)
-   Fetch API for backend communication
-   CSS Grid/Flexbox for responsive layout
-   ASCII art for circuit visualization

## Data Flow Patterns

### Circuit Generation Flow

```
1. User Request (width, gate_count)
   ↓
2. Factory Manager → Seed Generator
   ↓
3. SAT Synthesis (sat_revsynth)
   ↓
4. Circuit Creation + Validation
   ↓
5. Database Storage
   ↓
6. Representative Assignment
   ↓
7. API Response
```

### Circuit Unrolling Flow

```
1. User Request (circuit_id, max_equivalents)
   ↓
2. API → Factory Manager → Unroller
   ↓
3. Database → Circuit Record
   ↓
4. Record → sat_revsynth Circuit Object
   ↓
5. sat_revsynth.unroll() → Equivalent Circuits
   ↓
6. Circuit Objects → Database Storage
   ↓
7. API Response with Results
```

### Data Validation Flow

```
1. Database Read → Circuit Record
   ↓
2. Gate Data Validation
   ↓
3. Type Checking (list, tuple, int)
   ↓
4. Structure Validation
   ↓
5. sat_revsynth Circuit Creation
   ↓
6. Error Handling + Logging
```

## Key Algorithms

### 1. SAT-Based Circuit Generation

**Algorithm**: Uses `sat_revsynth` library for SAT-based synthesis
**Input**: Width (qubits), gate_count (gates)
**Output**: Identity circuit with specified dimensions

**Steps**:

1. Generate random forward circuit using SAT solver
2. Compute inverse circuit through gate reversal
3. Combine circuits: forward + inverse = identity
4. Validate identity property
5. Store in database with metadata

### 2. Circuit Unrolling

**Algorithm**: Uses `sat_revsynth` unrolling methods
**Input**: Representative circuit
**Output**: List of equivalent circuits

**Methods**:

-   `circuit.unroll([])`: Full unrolling space exploration
-   Swap space BFS: Explores gate swap possibilities
-   Rotations: Circuit rotation transformations
-   Permutations: Qubit permutation transformations

### 3. Representative Management

**Algorithm**: Intelligent circuit grouping and selection
**Input**: Circuits with same (width, gate_count)
**Output**: Representative circuits for each gate composition

**Process**:

1. Group circuits by gate composition (NOT, CNOT, CCNOT counts)
2. Select first circuit of each composition as representative
3. Mark representative with `representative_id = circuit_id`
4. Store equivalent relationships for other circuits

## Error Handling and Recovery

### Data Corruption Prevention

**Issue**: Malformed gate data in database
**Solution**: Robust validation in `_record_to_circuit()`

```python
def _record_to_circuit(self, record: CircuitRecord) -> Circuit:
    # Validate gate data structure
    if not isinstance(record.gates, list):
        raise TypeError(f"Malformed gates for circuit {record.id}")

    # Validate each gate
    for gate in record.gates:
        if not (isinstance(gate, (list, tuple)) and len(gate) == 2):
            raise TypeError(f"Malformed gate data: {gate}")
```

### Unrolling Error Recovery

**Issue**: Unrolling failures due to corrupted data
**Solution**: Graceful degradation with error logging

```python
try:
    equivalent_circuits = circuit.unroll([])
except Exception as e:
    logger.error(f"Unroll failed: {e}")
    return {"success": False, "equivalents": [], "error": str(e)}
```

### API Error Handling

**Pattern**: Consistent error responses with detailed logging

```python
try:
    result = perform_operation()
    return {"success": True, "data": result}
except Exception as e:
    logger.error(f"Operation failed: {e}")
    raise HTTPException(status_code=500, detail=str(e))
```

## Performance Considerations

### Database Optimization

**Indexing Strategy**:

-   Primary keys on all tables
-   Indexes on frequently queried columns
-   Composite indexes for complex queries

**Query Optimization**:

-   Use prepared statements
-   Limit result sets
-   Efficient JOIN operations

### Memory Management

**Circuit Storage**:

-   JSON serialization for gate data
-   Efficient data structures
-   Garbage collection for large operations

**Unrolling Limits**:

-   Configurable `max_equivalents` parameter
-   Memory monitoring for large operations
-   Background processing for heavy tasks

### Scalability Considerations

**Horizontal Scaling**:

-   Stateless API design
-   Database connection pooling
-   Job queue for background processing

**Vertical Scaling**:

-   Configurable worker processes
-   Memory-efficient algorithms
-   Caching strategies

## Security Considerations

### Input Validation

**API Inputs**:

-   Pydantic model validation
-   Type checking and bounds validation
-   SQL injection prevention

**Database Operations**:

-   Parameterized queries
-   Input sanitization
-   Access control

### Error Information

**Logging Strategy**:

-   Detailed error logging for debugging
-   Sanitized error messages for users
-   No sensitive data in logs

## Testing Strategy

### Unit Testing

**Component Testing**:

-   Individual class testing
-   Mock dependencies
-   Edge case coverage

**Integration Testing**:

-   API endpoint testing
-   Database integration testing
-   End-to-end workflow testing

### Performance Testing

**Load Testing**:

-   Concurrent request handling
-   Database performance under load
-   Memory usage monitoring

## Deployment Considerations

### Environment Setup

**Dependencies**:

-   Python 3.8+ required
-   SQLite3 database
-   SAT solver dependencies

**Configuration**:

-   Environment variable configuration
-   Database path configuration
-   Logging configuration

### Production Deployment

**Server Setup**:

-   FastAPI with uvicorn
-   Reverse proxy (nginx)
-   SSL/TLS configuration

**Monitoring**:

-   Application metrics
-   Database performance
-   Error tracking

## Future Enhancements

### Planned Features

1. **Advanced Circuit Analysis**:

    - Quantum circuit optimization
    - Error correction analysis
    - Performance benchmarking

2. **Enhanced Visualization**:

    - Interactive circuit diagrams
    - 3D circuit representations
    - Real-time animation

3. **Machine Learning Integration**:
    - Circuit complexity prediction
    - Optimization suggestions
    - Automated parameter tuning

### Technical Improvements

1. **Performance Optimization**:

    - Parallel processing
    - Caching strategies
    - Database optimization

2. **Scalability Enhancements**:

    - Distributed processing
    - Cloud deployment
    - Microservices architecture

3. **User Experience**:
    - Improved web interface
    - Mobile responsiveness
    - Advanced search and filtering

---

This documentation provides a comprehensive technical overview of the ID-Circuit system. For specific implementation details, refer to the individual component files and their inline documentation.
