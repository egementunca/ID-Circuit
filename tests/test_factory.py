import pytest
from pathlib import Path
import os

from identity_factory import IdentityFactory, FactoryConfig
from identity_factory.database import CircuitDatabase

# Fixture to create a temporary, clean database for each test function
@pytest.fixture
def test_db():
    """Create a temporary database for testing and tear it down afterward."""
    db_path = "test_factory.db"
    # Ensure no old test DB exists
    if os.path.exists(db_path):
        os.remove(db_path)
    
    db = CircuitDatabase(db_path=db_path)
    yield db
    
    # Teardown: close connection and remove the file
    del db
    if os.path.exists(db_path):
        os.remove(db_path)

# Fixture to create a factory instance with the test database
@pytest.fixture
def factory(test_db):
    """Create an IdentityFactory instance using the temporary database."""
    config = FactoryConfig(
        db_path=test_db.db_path,
        enable_debris_analysis=False,  # Disable for basic tests
        enable_ml_features=False  # Disable for basic tests
    )
    return IdentityFactory(config)

def test_factory_initialization(factory):
    """Test if the IdentityFactory initializes correctly."""
    assert factory is not None
    assert factory.db.db_path.name == "test_factory.db"
    assert isinstance(factory.db, CircuitDatabase)

def test_generate_single_circuit(factory):
    """Test the end-to-end generation of a single identity circuit."""
    # 1. Generate a new circuit
    result = factory.generate_identity_circuit(width=3, gate_count=2)

    assert result["success"] is True
    assert "error" not in result or result["error"] is None
    
    # 2. Verify database records
    seed_result = result.get("seed_generation")
    assert seed_result is not None
    
    dim_group_id = seed_result.dim_group_id
    circuit_id = seed_result.circuit_id
    
    assert dim_group_id is not None
    assert circuit_id is not None
    
    # Check dimension group
    dim_group = factory.db.get_dim_group_by_id(dim_group_id)
    assert dim_group is not None
    assert dim_group.width == 3
    assert dim_group.gate_count == 2
    assert dim_group.circuit_count >= 1  # At least the generated circuit
    
    # Check if circuit exists
    circuit = factory.db.get_circuit(circuit_id)
    assert circuit is not None
    assert circuit.width == 3
    assert circuit.gate_count == 2

def test_representative_creation(factory):
    """Test that representatives can be created and retrieved."""
    # Generate a circuit with representative creation
    result = factory.generate_identity_circuit(width=3, gate_count=3)
    
    assert result["success"] is True
    seed_result = result.get("seed_generation")
    dim_group_id = seed_result.dim_group_id
    
    # Check if representatives exist
    representatives = factory.db.get_representatives_for_dim_group(dim_group_id)
    
    # Should have at least one representative if unrolling was enabled
    if result.get("unrolling") and hasattr(result["unrolling"], "success") and result["unrolling"].success:
        assert len(representatives) >= 1
        
        # Check representative properties
        rep = representatives[0]
        assert rep.dim_group_id == dim_group_id
        assert rep.circuit_id is not None
        assert rep.gate_composition is not None

def test_unrolling_workflow(factory):
    """Test unrolling workflow with representatives."""
    # 1. Generate a circuit first
    gen_result = factory.generate_identity_circuit(width=3, gate_count=3)
    assert gen_result["success"], "Initial generation failed"
    
    dim_group_id = gen_result["seed_generation"].dim_group_id
    
    # 2. Get initial state
    dim_group_before = factory.db.get_dim_group_by_id(dim_group_id)
    representatives_before = factory.db.get_representatives_for_dim_group(dim_group_id)
    equivalents_before = factory.db.get_all_equivalents_for_dim_group(dim_group_id)
    
    # 3. Explicitly run unroller to generate more equivalents
    unroll_result = factory.unroller.unroll_dimension_group(dim_group_id)
    assert unroll_result.success
    
    # 4. Check that equivalents were generated
    equivalents_after = factory.db.get_all_equivalents_for_dim_group(dim_group_id)
    assert len(equivalents_after) >= len(equivalents_before)
    
    # 5. Verify equivalents point to representatives
    if equivalents_after:
        for equiv in equivalents_after:
            assert equiv.get('representative_id') is not None

def test_dimension_group_analysis(factory):
    """Test comprehensive dimension group analysis."""
    # 1. Generate a circuit and its equivalents
    result = factory.generate_identity_circuit(width=3, gate_count=4)
    assert result["success"]
    
    dim_group_id = result["seed_generation"].dim_group_id
    
    # 2. Get analysis
    analysis = factory.get_dimension_group_analysis(dim_group_id)
    
    assert "error" not in analysis
    assert analysis["dim_group_id"] == dim_group_id
    assert analysis["width"] == 3
    assert analysis["gate_count"] == 4
    assert analysis["circuit_count"] >= 1
    assert "representatives" in analysis
    assert "equivalents" in analysis

def test_database_consistency_after_run(factory):
    """Verify that database maintains consistency after operations."""
    # 1. Generate multiple circuits
    factory.generate_identity_circuit(width=3, gate_count=4)
    factory.generate_identity_circuit(width=4, gate_count=3)
    
    # 2. Get all dimension groups
    dim_groups = factory.db.get_all_dim_groups()
    assert len(dim_groups) >= 2
    
    # 3. Check each dimension group has proper structure
    for dim_group in dim_groups:
        # Check dimension group properties
        assert dim_group.width > 0
        assert dim_group.gate_count > 0
        assert dim_group.circuit_count >= 1
        
        # Check representatives
        representatives = factory.db.get_representatives_for_dim_group(dim_group.id)
        # Representatives may or may not exist depending on whether unrolling happened
        
        # Check equivalents
        equivalents = factory.db.get_all_equivalents_for_dim_group(dim_group.id)
        # Equivalents should point to valid representatives if they exist
        for equiv in equivalents:
            if equiv.get('representative_id'):
                rep_exists = any(rep.id == equiv['representative_id'] for rep in representatives)
                assert rep_exists, f"Equivalent points to non-existent representative {equiv['representative_id']}"

def test_batch_generation(factory):
    """Test batch generation of multiple circuits."""
    dimensions = [(3, 3), (3, 4), (4, 3)]
    
    results = factory.batch_generate(dimensions)
    
    assert len(results) == len(dimensions)
    
    successful_count = 0
    for (width, gate_count), result in results.items():
        assert "success" in result
        if result["success"]:
            successful_count += 1
            assert result["width"] == width
            assert result["gate_count"] == gate_count
    
    # At least some should succeed
    assert successful_count > 0

def test_factory_stats(factory):
    """Test factory statistics retrieval."""
    # Generate some circuits first
    factory.generate_identity_circuit(width=3, gate_count=3)
    factory.generate_identity_circuit(width=3, gate_count=4)
    
    stats = factory.get_factory_stats()
    
    assert stats.total_dim_groups >= 2
    assert stats.total_circuits >= 2
    assert stats.generation_time >= 0.0
    assert stats.unroll_time >= 0.0 