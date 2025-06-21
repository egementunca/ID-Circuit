import pytest
import multiprocessing
import time
import os
import httpx
import uvicorn

from identity_factory.api.server import create_app
from identity_factory.api.client import IdentityFactoryClientSync
from identity_factory.api.models import GenerateRequest

def _run_server(host: str, port: int, db_path: str):
    """Target function to run the Uvicorn server in a separate process."""
    # Set the DB path via environment variable so the factory within the app can pick it up
    os.environ["IDENTITY_FACTORY_DB_PATH"] = db_path
    # Disable ML/Debris features for faster, cleaner tests
    os.environ["IDENTITY_FACTORY_ENABLE_ML_FEATURES"] = "false"
    os.environ["IDENTITY_FACTORY_ENABLE_DEBRIS_ANALYSIS"] = "false"
    
    # Create and run the app
    app = create_app()
    uvicorn.run(app, host=host, port=port, log_level="warning")

@pytest.fixture(scope="session")
def live_api_server(tmp_path_factory):
    """
    Fixture to start a live API server for the duration of the test session.
    Uses a temporary database that is destroyed afterward.
    """
    db_path = str(tmp_path_factory.mktemp("data") / "test_api.db")
    host = "127.0.0.1"
    port = 8999  # Use a different port to avoid conflicts
    
    # Run the server in a separate process
    server_process = multiprocessing.Process(
        target=_run_server, args=(host, port, db_path), daemon=True
    )
    server_process.start()
    
    # Wait for the server to become available
    base_url = f"http://{host}:{port}"
    health_url = f"{base_url}/api/v1/health"
    is_ready = False
    for _ in range(20):  # Wait up to 10 seconds
        try:
            with httpx.Client() as client:
                response = client.get(health_url)
                if response.status_code == 200:
                    is_ready = True
                    break
        except httpx.ConnectError:
            time.sleep(0.5)
            
    if not is_ready:
        server_process.terminate()
        pytest.fail(f"API server at {base_url} did not start in time.")

    yield base_url
    
    # Teardown: stop the server
    server_process.terminate()
    server_process.join()

def test_api_health_check(live_api_server):
    """Test that the health endpoint works."""
    with httpx.Client() as client:
        response = client.get(f"{live_api_server}/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

def test_api_version(live_api_server):
    """Test that the version endpoint works."""
    with httpx.Client() as client:
        response = client.get(f"{live_api_server}/api/v1/version")
        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert "api_version" in data

def test_api_generate_circuit(live_api_server):
    """Test generating a single circuit via the API."""
    with httpx.Client() as client:
        request_data = {
            "width": 3,
            "gate_count": 3,
            "enable_unrolling": True,
            "enable_post_processing": True,
            "enable_debris_analysis": False,
            "enable_ml_analysis": False
        }
        
        response = client.post(
            f"{live_api_server}/api/v1/generate",
            json=request_data,
            timeout=30.0
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["width"] == 3
        assert data["gate_count"] == 3
        assert data["circuit_id"] is not None
        assert data["dim_group_id"] is not None
        assert data["generation_time"] >= 0.0

def test_api_list_dimension_groups(live_api_server):
    """Test listing dimension groups."""
    # First generate a circuit to have some data
    with httpx.Client() as client:
        # Generate a circuit
        request_data = {
            "width": 3,
            "gate_count": 4,
            "enable_unrolling": False,  # Disable for faster test
            "enable_post_processing": False,
            "enable_debris_analysis": False,
            "enable_ml_analysis": False
        }
        
        gen_response = client.post(
            f"{live_api_server}/api/v1/generate",
            json=request_data,
            timeout=30.0
        )
        assert gen_response.status_code == 200
        
        # List dimension groups
        list_response = client.get(f"{live_api_server}/api/v1/dimension-groups")
        assert list_response.status_code == 200
        
        data = list_response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        
        # Check first dimension group
        dim_group = data[0]
        assert "id" in dim_group
        assert "width" in dim_group
        assert "gate_count" in dim_group
        assert "circuit_count" in dim_group
        assert "representatives" in dim_group

def test_api_get_dimension_group(live_api_server):
    """Test getting a specific dimension group."""
    with httpx.Client() as client:
        # Generate a circuit first
        request_data = {
            "width": 3,
            "gate_count": 5,
            "enable_unrolling": False,
            "enable_post_processing": False,
            "enable_debris_analysis": False,
            "enable_ml_analysis": False
        }
        
        gen_response = client.post(
            f"{live_api_server}/api/v1/generate",
            json=request_data,
            timeout=30.0
        )
        assert gen_response.status_code == 200
        gen_data = gen_response.json()
        dim_group_id = gen_data["dim_group_id"]
        
        # Get the dimension group
        detail_response = client.get(f"{live_api_server}/api/v1/dimension-groups/{dim_group_id}")
        assert detail_response.status_code == 200
        
        data = detail_response.json()
        assert data["id"] == dim_group_id
        assert data["width"] == 3
        assert data["gate_count"] == 5
        assert data["circuit_count"] >= 1

def test_api_get_circuit(live_api_server):
    """Test getting a specific circuit."""
    with httpx.Client() as client:
        # Generate a circuit first
        request_data = {
            "width": 3,
            "gate_count": 3,
            "enable_unrolling": False,
            "enable_post_processing": False,
            "enable_debris_analysis": False,
            "enable_ml_analysis": False
        }
        
        gen_response = client.post(
            f"{live_api_server}/api/v1/generate",
            json=request_data,
            timeout=30.0
        )
        assert gen_response.status_code == 200
        gen_data = gen_response.json()
        circuit_id = gen_data["circuit_id"]
        
        # Get the circuit
        circuit_response = client.get(f"{live_api_server}/api/v1/circuits/{circuit_id}")
        assert circuit_response.status_code == 200
        
        data = circuit_response.json()
        assert data["id"] == circuit_id
        assert data["width"] == 3
        assert data["gate_count"] == 3
        assert "gates" in data
        assert "permutation" in data

def test_api_stats(live_api_server):
    """Test getting factory statistics."""
    with httpx.Client() as client:
        # Generate a circuit first to have some stats
        request_data = {
            "width": 3,
            "gate_count": 3,
            "enable_unrolling": False,
            "enable_post_processing": False,
            "enable_debris_analysis": False,
            "enable_ml_analysis": False
        }
        
        gen_response = client.post(
            f"{live_api_server}/api/v1/generate",
            json=request_data,
            timeout=30.0
        )
        assert gen_response.status_code == 200
        
        # Get stats
        stats_response = client.get(f"{live_api_server}/api/v1/stats")
        assert stats_response.status_code == 200
        
        data = stats_response.json()
        assert "total_dim_groups" in data
        assert "total_circuits" in data
        assert "total_representatives" in data
        assert "total_equivalents" in data
        assert data["total_dim_groups"] >= 1
        assert data["total_circuits"] >= 1

def test_api_batch_generate(live_api_server):
    """Test batch generation of circuits."""
    with httpx.Client() as client:
        request_data = {
            "dimensions": [
                {"width": 3, "gate_count": 3},
                {"width": 3, "gate_count": 4}
            ],
            "use_background": False,  # Synchronous for testing
            "use_job_queue": False,
            "enable_unrolling": False,
            "enable_post_processing": False,
            "enable_debris_analysis": False,
            "enable_ml_analysis": False
        }
        
        response = client.post(
            f"{live_api_server}/api/v1/batch-generate",
            json=request_data,
            timeout=60.0
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["total_requested"] == 2
        assert data["status"] == "completed"
        assert "results" in data 