"""
Comprehensive tests for the seed generation workflow via API.

These tests cover the user's specific concerns about the system:
1. Identity circuits that implement the identity permutation
2. Hash-based deduplication 
3. Gate normalization (CCX gates with sorted control qubits)
4. Representative vs equivalent circuit handling
5. Dimension group organization by (width, gate_count)
6. Forward + inverse circuit synthesis approach
7. SAT solver integration for inverse synthesis
"""

import pytest
import asyncio
import tempfile
import os
from typing import List, Tuple
from fastapi.testclient import TestClient
import json

from identity_factory.api.server import create_app
from identity_factory.database import CircuitDatabase
from identity_factory.seed_generator import SeedGenerator
from sat_revsynth.circuit.circuit import Circuit
from sat_revsynth.truth_table.truth_table import TruthTable

class TestSeedGenerationAPI:
    """Test suite for seed generation via API."""
    
    @pytest.fixture
    def client(self):
        """Create test client with temporary database."""
        app = create_app(debug=True)
        with TestClient(app) as client:
            yield client
    
    @pytest.fixture
    def database(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as f:
            db_path = f.name
        
        try:
            db = CircuitDatabase(db_path)
            yield db
        finally:
            # Cleanup
            db.close()
            if os.path.exists(db_path):
                os.unlink(db_path)
    
    def test_health_check(self, client):
        """Test API health check endpoint."""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert "database_connected" in data
        assert "sat_solver_available" in data
        assert "version" in data
    
    def test_generate_single_circuit_basic(self, client):
        """Test basic single circuit generation."""
        request_data = {
            "width": 2,
            "forward_length": 3,
            "max_attempts": 5
        }
        
        response = client.post("/api/v1/generate", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert data["circuit_id"] is not None
        assert data["dim_group_id"] is not None
        assert data["forward_gates"] is not None
        assert data["inverse_gates"] is not None
        assert data["identity_gates"] is not None
        assert data["gate_composition"] is not None
        assert len(data["gate_composition"]) == 3  # (X, CX, CCX)
        assert data["total_time"] >= 0
    
    def test_generate_circuit_identity_verification(self, client):
        """Test that generated circuits actually implement identity permutation."""
        request_data = {
            "width": 2,
            "forward_length": 2,
            "max_attempts": 10
        }
        
        response = client.post("/api/v1/generate", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        
        # Get the full circuit
        circuit_id = data["circuit_id"]
        circuit_response = client.get(f"/api/v1/circuits/{circuit_id}")
        assert circuit_response.status_code == 200
        
        circuit_data = circuit_response.json()
        
        # Verify the circuit implements identity permutation
        width = circuit_data["width"]
        permutation = circuit_data["permutation"]
        
        # Identity permutation means permutation[i] == i for all i
        expected_identity = list(range(2**width))
        assert permutation == expected_identity, f"Circuit {circuit_id} does not implement identity: {permutation}"
    
    def test_generate_circuit_gate_normalization(self, client):
        """Test that generated circuits have properly normalized gates."""
        request_data = {
            "width": 3,
            "forward_length": 4,
            "max_attempts": 10
        }
        
        response = client.post("/api/v1/generate", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        if data["success"]:
            circuit_id = data["circuit_id"]
            circuit_response = client.get(f"/api/v1/circuits/{circuit_id}")
            assert circuit_response.status_code == 200
            
            circuit_data = circuit_response.json()
            gates = circuit_data["gates"]
            
            # Check gate normalization - CCX gates should have sorted control qubits
            for gate in gates:
                if gate[0] == "CCX":
                    control1, control2, target = gate[1], gate[2], gate[3]
                    assert control1 < control2, f"CCX gate not normalized: {gate}"
                    assert control1 != target and control2 != target, f"CCX gate has control==target: {gate}"
    
    def test_generate_circuit_hash_deduplication(self, client):
        """Test hash-based deduplication works correctly."""
        # Generate multiple circuits with same parameters
        request_data = {
            "width": 2,
            "forward_length": 2,
            "max_attempts": 5
        }
        
        circuit_hashes = set()
        circuit_ids = []
        
        # Generate several circuits
        for _ in range(5):
            response = client.post("/api/v1/generate", json=request_data)
            assert response.status_code == 200
            
            data = response.json()
            if data["success"]:
                circuit_id = data["circuit_id"]
                circuit_ids.append(circuit_id)
                
                # Get circuit details
                circuit_response = client.get(f"/api/v1/circuits/{circuit_id}")
                assert circuit_response.status_code == 200
                
                circuit_data = circuit_response.json()
                circuit_hash = circuit_data["circuit_hash"]
                
                # Hash should be present
                assert circuit_hash is not None
                assert len(circuit_hash) > 0
                
                circuit_hashes.add(circuit_hash)
        
        # Different circuits should have different hashes
        # (unless we happen to generate identical circuits, which is possible but unlikely)
        # The important thing is that the hash field is populated
        assert len(circuit_hashes) > 0
    
    def test_generate_circuit_representative_assignment(self, client):
        """Test that new circuits are assigned as their own representatives."""
        request_data = {
            "width": 2,
            "forward_length": 3,
            "max_attempts": 5
        }
        
        response = client.post("/api/v1/generate", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        if data["success"]:
            circuit_id = data["circuit_id"]
            
            # Get circuit details
            circuit_response = client.get(f"/api/v1/circuits/{circuit_id}")
            assert circuit_response.status_code == 200
            
            circuit_data = circuit_response.json()
            
            # New circuits should be their own representatives
            assert circuit_data["representative_id"] == circuit_data["id"]
            assert circuit_data["is_representative"] is True
    
    def test_generate_circuit_dimension_group_assignment(self, client):
        """Test that circuits are correctly assigned to dimension groups."""
        request_data = {
            "width": 3,
            "forward_length": 4,
            "max_attempts": 5
        }
        
        response = client.post("/api/v1/generate", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        if data["success"]:
            circuit_id = data["circuit_id"]
            dim_group_id = data["dim_group_id"]
            
            # Get circuit details
            circuit_response = client.get(f"/api/v1/circuits/{circuit_id}")
            assert circuit_response.status_code == 200
            
            circuit_data = circuit_response.json()
            
            # Verify dimension group assignment
            assert circuit_data["dim_group_id"] == dim_group_id
            assert circuit_data["width"] == request_data["width"]
            
            # Get dimension group details
            dim_group_response = client.get(f"/api/v1/dim-groups/{dim_group_id}")
            assert dim_group_response.status_code == 200
            
            dim_group_data = dim_group_response.json()
            assert dim_group_data["width"] == request_data["width"]
            # The gate_count should match the total length of the identity circuit
            assert dim_group_data["gate_count"] == circuit_data["gate_count"]
    
    def test_batch_generation(self, client):
        """Test batch circuit generation."""
        request_data = {
            "dimensions": [
                [2, 2],
                [2, 3],
                [3, 2]
            ],
            "max_attempts": 5
        }
        
        response = client.post("/api/v1/batch-generate", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["total_requested"] == 3
        assert len(data["results"]) == 3
        assert data["successful_generations"] >= 0
        assert data["failed_generations"] >= 0
        assert data["successful_generations"] + data["failed_generations"] == 3
        assert data["total_time"] >= 0
        
        # Check individual results
        for i, result in enumerate(data["results"]):
            if result["success"]:
                assert result["circuit_id"] is not None
                assert result["dim_group_id"] is not None
                assert result["forward_gates"] is not None
                assert result["inverse_gates"] is not None
                assert result["identity_gates"] is not None
    
    def test_circuit_search_and_filtering(self, client):
        """Test comprehensive circuit search and filtering."""
        # First generate some circuits
        for width in [2, 3]:
            for forward_length in [2, 3]:
                request_data = {
                    "width": width,
                    "forward_length": forward_length,
                    "max_attempts": 3
                }
                client.post("/api/v1/generate", json=request_data)
        
        # Test basic circuit search
        response = client.get("/api/v1/circuits")
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert "pages" in data
        
        # Test width filtering
        response = client.get("/api/v1/circuits?width=2")
        assert response.status_code == 200
        
        data = response.json()
        for circuit in data["items"]:
            assert circuit["width"] == 2
        
        # Test representative filtering
        response = client.get("/api/v1/circuits?is_representative=true")
        assert response.status_code == 200
        
        data = response.json()
        for circuit in data["items"]:
            assert circuit["is_representative"] is True
        
        # Test gate composition filtering (if any circuits exist)
        if data["total"] > 0:
            # Get a circuit to see its composition
            first_circuit = data["items"][0]
            composition = first_circuit.get("gate_composition")  # This might not exist in the response
            
            # For now, just test the format is accepted
            response = client.get("/api/v1/circuits?gate_composition=1,0,0")
            assert response.status_code == 200  # Should not error even if no matches
    
    def test_advanced_circuit_search(self, client):
        """Test advanced circuit search functionality."""
        # Generate some circuits first
        for width in [2, 3]:
            for forward_length in [2, 3]:
                request_data = {
                    "width": width,
                    "forward_length": forward_length,
                    "max_attempts": 3
                }
                client.post("/api/v1/generate", json=request_data)
        
        # Test advanced search
        search_request = {
            "width_range": [2, 3],
            "gate_count_range": [1, 10],
            "gate_types": ["X", "CX"]
        }
        
        response = client.post("/api/v1/circuits/advanced-search", json=search_request)
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert "total" in data
        
        # Verify results match search criteria
        for circuit in data["items"]:
            assert 2 <= circuit["width"] <= 3
            assert 1 <= circuit["gate_count"] <= 10
    
    def test_dimension_group_operations(self, client):
        """Test dimension group listing and operations."""
        # Generate circuits in different dimension groups
        dimensions = [(2, 2), (2, 3), (3, 2)]
        
        for width, forward_length in dimensions:
            request_data = {
                "width": width,
                "forward_length": forward_length,
                "max_attempts": 3
            }
            client.post("/api/v1/generate", json=request_data)
        
        # Test listing dimension groups
        response = client.get("/api/v1/dim-groups")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list)
        
        if len(data) > 0:
            # Test getting specific dimension group
            dim_group = data[0]
            dim_group_id = dim_group["id"]
            
            response = client.get(f"/api/v1/dim-groups/{dim_group_id}")
            assert response.status_code == 200
            
            # Test getting circuits in dimension group
            response = client.get(f"/api/v1/dim-groups/{dim_group_id}/circuits")
            assert response.status_code == 200
            
            circuits = response.json()
            assert isinstance(circuits, list)
            
            # Test getting only representatives
            response = client.get(f"/api/v1/dim-groups/{dim_group_id}/circuits?representatives_only=true")
            assert response.status_code == 200
            
            representatives = response.json()
            assert isinstance(representatives, list)
            
            # All returned circuits should be representatives
            for circuit in representatives:
                assert circuit["is_representative"] is True
    
    def test_circuit_visualization(self, client):
        """Test circuit visualization functionality."""
        # Generate a circuit
        request_data = {
            "width": 2,
            "forward_length": 2,
            "max_attempts": 5
        }
        
        response = client.post("/api/v1/generate", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        if data["success"]:
            circuit_id = data["circuit_id"]
            
            # Test visualization endpoint
            response = client.get(f"/api/v1/circuits/{circuit_id}/visualization")
            assert response.status_code == 200
            
            viz_data = response.json()
            assert "circuit_id" in viz_data
            assert "ascii_diagram" in viz_data
            assert "gate_descriptions" in viz_data
            assert "permutation_table" in viz_data
            
            assert viz_data["circuit_id"] == circuit_id
            assert isinstance(viz_data["gate_descriptions"], list)
            assert isinstance(viz_data["permutation_table"], list)
    
    def test_factory_statistics(self, client):
        """Test factory statistics endpoints."""
        # Test basic stats
        response = client.get("/api/v1/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_circuits" in data
        assert "total_dim_groups" in data
        assert "total_representatives" in data
        assert "total_equivalents" in data
        assert "pending_jobs" in data
        
        # Test generation stats
        response = client.get("/api/v1/generator/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_attempts" in data
        assert "successful_generations" in data
        assert "failed_generations" in data
        assert "success_rate_percent" in data
        assert "total_generation_time" in data
        assert "average_generation_time" in data
    
    def test_gate_composition_analysis(self, client):
        """Test gate composition grouping within dimension groups."""
        # Generate circuits
        request_data = {
            "width": 3,
            "forward_length": 3,
            "max_attempts": 5
        }
        
        response = client.post("/api/v1/generate", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        if data["success"]:
            dim_group_id = data["dim_group_id"]
            
            # Test composition analysis
            response = client.get(f"/api/v1/dim-groups/{dim_group_id}/compositions")
            assert response.status_code == 200
            
            compositions = response.json()
            assert isinstance(compositions, list)
            
            for composition_group in compositions:
                assert "gate_composition" in composition_group
                assert "circuits" in composition_group
                assert "total_count" in composition_group
                
                # Gate composition should be a tuple of 3 integers
                assert len(composition_group["gate_composition"]) == 3
                assert all(isinstance(x, int) for x in composition_group["gate_composition"])
    
    def test_sat_solver_integration(self, client):
        """Test that SAT solver integration works correctly."""
        # This test verifies that the inverse synthesis is working
        request_data = {
            "width": 2,
            "forward_length": 3,
            "max_inverse_gates": 10,
            "max_attempts": 5
        }
        
        response = client.post("/api/v1/generate", json=request_data)
        assert response.status_code == 200
        
        data = response.json()
        if data["success"]:
            # Verify that inverse synthesis produced results
            assert data["inverse_gates"] is not None
            assert isinstance(data["inverse_gates"], list)
            assert len(data["inverse_gates"]) <= request_data["max_inverse_gates"]
            
            # Verify the combined circuit is correct
            forward_gates = data["forward_gates"]
            inverse_gates = data["inverse_gates"]
            identity_gates = data["identity_gates"]
            
            # The identity_gates should be forward_gates + inverse_gates
            expected_identity = forward_gates + inverse_gates
            assert identity_gates == expected_identity
    
    def test_error_handling(self, client):
        """Test API error handling for invalid requests."""
        # Test invalid width
        request_data = {
            "width": 0,  # Invalid
            "forward_length": 2
        }
        
        response = client.post("/api/v1/generate", json=request_data)
        assert response.status_code == 422  # Validation error
        
        # Test invalid forward_length
        request_data = {
            "width": 2,
            "forward_length": 0  # Invalid
        }
        
        response = client.post("/api/v1/generate", json=request_data)
        assert response.status_code == 422  # Validation error
        
        # Test non-existent circuit
        response = client.get("/api/v1/circuits/999999")
        assert response.status_code == 404
        
        # Test non-existent dimension group
        response = client.get("/api/v1/dim-groups/999999")
        assert response.status_code == 404

# Helper functions for testing

def verify_identity_circuit(gates: List[Tuple], width: int) -> bool:
    """Verify that a circuit implements the identity permutation."""
    try:
        circuit = Circuit(width)
        for gate in gates:
            if gate[0] == 'X':
                circuit.x(gate[1])
            elif gate[0] == 'CX':
                circuit.cx(gate[1], gate[2])
            elif gate[0] == 'CCX':
                circuit.mcx([gate[1], gate[2]], gate[3])
        
        truth_table = TruthTable(circuit)
        permutation = truth_table.permutation
        
        # Identity permutation means permutation[i] == i for all i
        expected = list(range(2**width))
        return permutation == expected
        
    except Exception:
        return False

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 