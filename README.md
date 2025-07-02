# ID-Circuit: Identity Circuit Factory

A comprehensive system for generating, analyzing, and managing quantum identity circuits using SAT-based synthesis and advanced circuit transformation techniques.

## Overview

ID-Circuit is a sophisticated quantum circuit generation and analysis platform that leverages the `sat_revsynth` library to create identity circuits and explore their equivalent representations. The system provides a REST API for circuit generation and analysis, along with a modern Next.js web interface for visualization and interaction.

## Features

-   **SAT-Based Circuit Generation**: Generate identity circuits using advanced SAT synthesis
-   **Forward-Inverse Circuit Synthesis**: Create forward circuits and synthesize their inverses
-   **Circuit Database Management**: Efficient SQLite-based storage with circuit deduplication
-   **Dimension Group Analysis**: Organize circuits by width and gate count
-   **Gate Composition Tracking**: Analyze circuits by (NOT, CNOT, CCNOT) gate counts
-   **REST API**: Full-featured FastAPI-based API for programmatic access
-   **Modern Web Interface**: Next.js frontend with TypeScript and Tailwind CSS
-   **Circuit Visualization**: ASCII diagrams and interactive circuit displays

## Architecture

### Core Components

1. **Seed Generator** (`identity_factory/seed_generator.py`): SAT-based identity circuit generation
2. **Database Layer** (`identity_factory/database.py`): SQLite-based persistence with circuit management
3. **API Server** (`identity_factory/api/`): FastAPI-based REST API
4. **Web Interface** (`frontend-next/`): Modern Next.js frontend with TypeScript
5. **SAT Synthesis** (`sat_revsynth/`): Core library for circuit synthesis and manipulation

### Data Model

-   **Circuit Records**: Individual circuits with gates, permutation data, and metadata
-   **Dimension Groups**: Collections of circuits with same (width, length)
-   **Gate Compositions**: Analysis by gate type counts
-   **Representatives**: Circuits serving as representatives for their gate composition

## Quick Start

### Prerequisites

-   Python 3.8+ (Python 3.12 recommended)
-   Node.js 18+ (for frontend)
-   Git

### Installation

1. **Clone the repository**:

    ```bash
    git clone <repository-url>
    cd ID-Circuit
    ```

2. **Run the setup script**:

    ```bash
    chmod +x setup.sh
    ./setup.sh
    ```

3. **Activate the environment**:

    ```bash
    source .venv/bin/activate
    ```

4. **Start the API server**:

    ```bash
    python start_api.py
    ```

5. **Set up and start the frontend** (in a new terminal):

    ```bash
    cd frontend-next
    npm install
    npm run dev
    ```

6. **Access the application**:
    - Frontend: http://localhost:3000
    - API: http://localhost:8000
    - API Documentation: http://localhost:8000/docs

### Basic Usage

#### Generate a Circuit via API

```python
import requests

# Generate a 3-qubit circuit with 4 gates
response = requests.post("http://localhost:8000/api/v1/circuits/generate", json={
    "width": 3,
    "forward_length": 4
})

circuit_data = response.json()
print(f"Generated circuit ID: {circuit_data['circuit_id']}")
```

#### Get Circuit Visualization

```python
# Get circuit ASCII representation
response = requests.get(f"http://localhost:8000/api/v1/circuits/{circuit_id}/ascii")
ascii_data = response.json()
print(ascii_data['ascii_diagram'])
```

#### List Dimension Groups

```python
# Get available dimension groups
response = requests.get("http://localhost:8000/api/v1/dim-groups")
dim_groups = response.json()
for group in dim_groups['dim_groups']:
    print(f"Width: {group['width']}, Length: {group['length']}, Count: {group['circuit_count']}")
```

## API Reference

### Core Endpoints

-   `POST /api/v1/circuits/generate` - Generate new identity circuits
-   `GET /api/v1/dim-groups` - List dimension groups with circuit counts
-   `GET /api/v1/dim-groups/{id}/circuits` - Get circuits for a dimension group
-   `GET /api/v1/circuits/{id}` - Get circuit details
-   `GET /api/v1/circuits/{id}/ascii` - Get ASCII representation of a circuit
-   `GET /api/v1/stats/summary` - Get system-wide statistics
-   `GET /health` - Health check endpoint

### Frontend Features

-   **Circuit Generation**: Interactive form for generating circuits with specified parameters
-   **Circuit Visualization**: ASCII diagrams and structured gate displays
-   **Dimension Groups**: Browse circuits organized by width and length
-   **Statistics Dashboard**: Overview of generated circuits and system status
-   **Responsive Design**: Modern UI that works on desktop and mobile

## Configuration

The system can be configured through environment variables or by modifying settings in the respective modules:

### Backend Configuration

-   Database location: `identity_circuits.db` (configurable in `database.py`)
-   API server: Host and port settings in `start_api.py`
-   Generation limits: Configurable in `seed_generator.py`

### Frontend Configuration

-   API endpoint: Configured in `frontend-next/src/lib/api.ts`
-   UI settings: Tailwind CSS configuration in `frontend-next/tailwind.config.js`

## Database Schema

The system uses SQLite with the following main tables:

-   `circuits`: Individual circuit data with gates, permutation, and metadata
-   `dim_groups`: Dimension group definitions (width, length)
-   `dim_group_circuits`: Many-to-many relationship between circuits and dimension groups

## Development

### Project Structure

```
ID-Circuit/
├── identity_factory/          # Main Python package
│   ├── api/                  # FastAPI REST API
│   ├── database.py           # Database layer
│   ├── seed_generator.py     # Circuit generation
│   └── ...
├── sat_revsynth/            # SAT-based synthesis library
├── frontend-next/           # Next.js frontend
│   ├── src/
│   │   ├── app/            # Next.js 13+ app directory
│   │   ├── components/     # React components
│   │   └── types/          # TypeScript types
│   └── ...
├── tests/                   # Test suite
├── start_api.py            # API server launcher
└── setup.sh               # Setup script
```

### Development Commands

```bash
# Backend development
source .venv/bin/activate
python start_api.py          # Start API server
pytest                       # Run tests
black .                      # Format code
flake8 .                     # Lint code

# Frontend development
cd frontend-next
npm run dev                  # Development server
npm run build                # Production build
npm run type-check           # TypeScript checking
```

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Add tests for new functionality
5. Run the test suite: `pytest`
6. Format code: `black .`
7. Submit a pull request

### Testing

Run the test suite:

```bash
# Backend tests
pytest

# Frontend tests (if implemented)
cd frontend-next
npm test
```

## Performance Considerations

-   **Circuit Generation**: Time scales with circuit complexity and synthesis difficulty
-   **Database Operations**: Optimized with proper indexing and hash-based deduplication
-   **Memory Usage**: Consider circuit count limits for large-scale operations
-   **Frontend**: React components optimized for rendering large lists of circuits

## Known Limitations

1. **SAT Solver Dependencies**: Requires proper installation of SAT solving libraries
2. **Memory Usage**: Large circuit databases may require memory optimization
3. **Synthesis Time**: Complex circuits may take longer to synthesize
4. **Browser Compatibility**: Frontend requires modern browser with ES2020+ support

## License

MIT License - see LICENSE file for details

## Acknowledgments

-   Built on the `sat_revsynth` library for SAT-based circuit synthesis
-   Uses FastAPI for the REST API framework
-   Frontend built with Next.js, React, and Tailwind CSS
-   Database operations powered by SQLite

## Support

For issues, questions, or contributions:

1. Check the [Issues](https://github.com/yourusername/ID-Circuit/issues) page
2. Review the API documentation at `/docs`
3. Check the setup script and installation instructions
4. Contact the development team

---

**Note**: This system is designed for research and educational purposes in quantum circuit analysis and synthesis.
