# Identity Circuit Factory

A comprehensive system for generating, analyzing, and managing quantum identity circuits using SAT-based synthesis and advanced post-processing techniques.

## 🏗️ Repository Structure

This repository contains two main components that work together:

### 1. **Identity Factory** (`identity_factory/`)

The main application for generating and managing identity circuits.

### 2. **SAT Reversible Synthesis** (`sat_revsynth/`)

A specialized library for SAT-based circuit synthesis that the Identity Factory uses.

---

## 📁 Detailed Component Breakdown

### Identity Factory (`identity_factory/`)

The core application that orchestrates the entire identity circuit generation process.

#### **Core Components:**

-   **`factory_manager.py`** - Main orchestrator class that coordinates all operations
-   **`database.py`** - SQLite database management for storing circuits and metadata
-   **`seed_generator.py`** - Generates identity circuits and manages representatives
-   **`unroller.py`** - Creates equivalent circuits from representative circuits
-   **`post_processor.py`** - Simplifies and optimizes circuits
-   **`debris_cancellation.py`** - Analyzes and removes redundant gates
-   **`ml_features.py`** - Extracts machine learning features from circuits

#### **API Layer (`identity_factory/api/`):**

-   **`server.py`** - FastAPI server implementation
-   **`endpoints.py`** - REST API endpoint definitions
-   **`client.py`** - Python client library for API interaction
-   **`models.py`** - Pydantic models for API requests/responses

#### **Utilities:**

-   **`cli.py`** - Command-line interface for direct usage
-   **`job_queue.py`** - Background job processing system

### SAT Reversible Synthesis (`sat_revsynth/`)

A specialized library for SAT-based circuit synthesis that provides the core synthesis capabilities.

#### **Core Components:**

-   **`circuit/`** - Circuit representation and manipulation
    -   `circuit.py` - Main Circuit class with gates and operations
    -   `collection.py` - Manages collections of circuits
    -   `dim_group.py` - Dimension groups for organizing circuits
-   **`sat/`** - SAT solving infrastructure
    -   `cnf.py` - CNF formula representation
    -   `solver.py` - SAT solver interface
-   **`synthesizers/`** - Circuit synthesis algorithms
    -   `circuit_synthesizer.py` - Individual circuit synthesis
    -   `collection_synthesizer.py` - Batch circuit synthesis
    -   `dimgroup_synthesizer.py` - Dimension group synthesis
    -   `optimal_synthesizer.py` - Optimal circuit synthesis
-   **`truth_table/`** - Truth table representation and operations
-   **`utils/`** - Utility functions

---

## 🔧 Installation & Setup

### Prerequisites

-   Python 3.8+
-   pip

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd ID-Circuit

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install the project in editable mode
pip install -e .
```

### Verification

```bash
# Run tests to verify everything works
pytest

# Test the CLI
python -m identity_factory --help
```

---

## 🚀 Usage

### Command Line Interface

```bash
# Generate a simple identity circuit
python -m identity_factory generate 3 5

# Get statistics
python -m identity_factory stats

# List dimension groups and their representatives
python -m identity_factory list --show-representatives

# Unroll a dimension group to generate equivalents
python -m identity_factory unroll 1

# Analyze a dimension group
python -m identity_factory analyze 1
```

### API Server

```bash
# Start the API server
python start_api.py --host 0.0.0.0 --port 8000

# The server provides:
# - REST API at http://localhost:8000/api/v1/
# - Interactive docs at http://localhost:8000/docs
```

### Python API

```python
from identity_factory import IdentityFactory

# Create factory instance
factory = IdentityFactory()

# Generate a circuit
result = factory.generate_identity_circuit(width=3, gate_count=5)
print(f"Generated circuit with {result['total_equivalents']} equivalents")
```

---

## 🔄 Workflow

The Identity Circuit Factory follows this workflow:

1. **Identity Circuit Generation**: SAT synthesis creates identity circuits with specified dimensions
2. **Dimension Group Organization**: Circuits are organized by (width, gate_count) dimensions
3. **Representative Selection**: Some circuits are chosen as representatives for further processing
4. **Unrolling**: Representatives generate equivalent circuits through transformations
5. **Post-processing**: Circuits are simplified and optimized
6. **Analysis**: ML features and debris analysis are performed
7. **Storage**: Results are stored in the database with proper relationships

## 🏗️ Core Concepts

### Dimension Groups

A dimension group is a collection of identity circuits that share the same (width, gate_count) dimensions. Multiple different identity circuits can exist in the same dimension group if they have different gate compositions.

### Representatives

Representatives are specific circuits chosen from a dimension group to generate equivalent circuits. A dimension group can have multiple representatives with different gate compositions.

### Equivalents

Equivalent circuits are generated from representatives through various transformations (swaps, rotations, permutations, etc.). These circuits maintain the identity property while having different gate arrangements.

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run specific test categories
pytest tests/test_factory.py    # Backend logic tests
pytest tests/test_api.py        # API integration tests

# Run with coverage
pytest --cov=identity_factory --cov=sat_revsynth
```

---

## 📊 Database Schema

The system uses SQLite with the following main tables:

-   `circuits` - Individual circuit data
-   `dim_groups` - Dimension groups organizing circuits by (width, gate_count)
-   `representatives` - Representative circuits chosen from dimension groups
-   `circuit_equivalents` - Equivalent circuits generated from representatives
-   `simplifications` - Circuit simplification records
-   `debris_cancellation_records` - Debris analysis results
-   `ml_features` - Machine learning features
-   `jobs` - Background job tracking

### Key Relationships

-   Dimension groups contain multiple identity circuits
-   Representatives are chosen from circuits within dimension groups
-   Equivalents are generated from representatives and point back to them
-   All circuits maintain their dimensional grouping

---

## 🔧 Configuration

Configuration is handled through the `FactoryConfig` class in `factory_manager.py`:

```python
from identity_factory import FactoryConfig, IdentityFactory

config = FactoryConfig(
    db_path="my_circuits.db",
    max_inverse_gates=40,
    enable_post_processing=True,
    enable_ml_features=True
)

factory = IdentityFactory(config)
```

---

## 🚀 Deployment

### Local Development

```bash
pip install -e .
python start_api.py
```

### Production

```bash
# Install dependencies
pip install -r requirements.txt

# Run with production server
uvicorn identity_factory.api.server:app --host 0.0.0.0 --port 8000
```

---

## 📝 Development

### Adding New Features

1. Add code to appropriate module in `identity_factory/`
2. Add tests in `tests/`
3. Update API models if needed
4. Run tests to verify

### Code Quality

```bash
# Format code
black identity_factory/ sat_revsynth/

# Lint code
flake8 identity_factory/ sat_revsynth/

# Type checking
mypy identity_factory/ sat_revsynth/
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run the full test suite
5. Submit a pull request

---

## 📄 License

[Add your license information here]
