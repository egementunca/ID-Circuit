#!/usr/bin/env python3
"""
Example usage of the Identity Circuit Factory.

This script demonstrates how to use the factory programmatically
to generate, unroll, and simplify identity circuits using the corrected design.
"""

import sys
import time
from pathlib import Path

# Add the current directory to the path so we can import our modules
sys.path.insert(0, str(Path(__file__).parent))

from identity_factory import IdentityFactory, FactoryConfig

def example_basic_generation():
    """Example of basic identity circuit generation."""
    print("=== Basic Identity Circuit Generation ===")
    
    # Create factory configuration
    config = FactoryConfig(
        db_path="example_circuits.db",
        max_inverse_gates=30,
        max_equivalents=1000,
        enable_debris_analysis=False,  # Disable for examples
        enable_ml_features=False
    )
    
    # Initialize factory
    factory = IdentityFactory(config)
    
    # Generate a single identity circuit
    print("Generating identity circuit for width=3, gate_count=5...")
    result = factory.generate_identity_circuit(width=3, gate_count=5)
    
    if result["success"]:
        seed_result = result["seed_generation"]
        print(f"✓ Success! Generated in {result['total_time']:.2f}s")
        print(f"  Circuit ID: {seed_result.circuit_id}")
        print(f"  Dimension group ID: {seed_result.dim_group_id}")
        
        if result.get("unrolling"):
            print(f"  Equivalents generated: {result['unrolling'].total_equivalents}")
        
        if result.get("post_processing"):
            print(f"  Simplifications performed: {len(result.get('post_processing', []))}")
    else:
        print(f"✗ Failed: {result.get('error', 'Unknown error')}")

def example_dimension_group_analysis():
    """Example of analyzing a dimension group."""
    print("\n=== Dimension Group Analysis ===")
    
    config = FactoryConfig(
        db_path="example_circuits.db",
        enable_debris_analysis=False,
        enable_ml_features=False
    )
    
    factory = IdentityFactory(config)
    
    # Generate a circuit first
    result = factory.generate_identity_circuit(width=3, gate_count=4)
    
    if result["success"]:
        dim_group_id = result["seed_generation"].dim_group_id
        
        # Analyze the dimension group
        analysis = factory.get_dimension_group_analysis(dim_group_id)
        
        print(f"Analysis for dimension group {dim_group_id}:")
        print(f"  Width: {analysis['width']}")
        print(f"  Gate count: {analysis['gate_count']}")
        print(f"  Circuit count: {analysis['circuit_count']}")
        print(f"  Representatives: {len(analysis['representatives'])}")
        print(f"  Total equivalents: {analysis['total_equivalents']}")
        
        # Show representative details
        for i, rep in enumerate(analysis['representatives']):
            print(f"  Representative {i+1}:")
            print(f"    Circuit ID: {rep['circuit_id']}")
            print(f"    Gate composition: {rep['gate_composition']}")
            print(f"    Is primary: {rep['is_primary']}")

def example_batch_generation():
    """Example of batch generation for multiple dimensions."""
    print("\n=== Batch Generation ===")
    
    config = FactoryConfig(
        db_path="example_circuits.db",
        max_inverse_gates=25,
        max_equivalents=500,
        enable_debris_analysis=False,
        enable_ml_features=False
    )
    
    factory = IdentityFactory(config)
    
    # Define dimensions to generate
    dimensions = [(3, 4), (3, 5), (4, 4), (4, 5)]
    
    print(f"Generating circuits for {len(dimensions)} dimensions...")
    results = factory.batch_generate(dimensions)
    
    successful = sum(1 for r in results.values() if r["success"])
    print(f"✓ Generated {successful}/{len(dimensions)} dimension groups successfully")
    
    for (width, gate_count), result in results.items():
        if result["success"]:
            print(f"  ({width}, {gate_count}): ✓ Success")
        else:
            print(f"  ({width}, {gate_count}): ✗ Failed")

def example_unrolling():
    """Example of unrolling a dimension group to generate equivalents."""
    print("\n=== Manual Unrolling ===")
    
    config = FactoryConfig(
        db_path="example_circuits.db",
        enable_debris_analysis=False,
        enable_ml_features=False
    )
    
    factory = IdentityFactory(config)
    
    # Generate a circuit without unrolling
    print("Generating circuit without unrolling...")
    result = factory.generate_identity_circuit(
        width=3, 
        gate_count=6,
        enable_unrolling=False
    )
    
    if result["success"]:
        dim_group_id = result["seed_generation"].dim_group_id
        
        # Check initial state
        analysis_before = factory.get_dimension_group_analysis(dim_group_id)
        print(f"Before unrolling: {analysis_before['total_equivalents']} equivalents")
        
        # Manually unroll the dimension group
        print("Unrolling dimension group...")
        unroll_result = factory.unroller.unroll_dimension_group(dim_group_id)
        
        if unroll_result.success:
            analysis_after = factory.get_dimension_group_analysis(dim_group_id)
            print(f"After unrolling: {analysis_after['total_equivalents']} equivalents")
            print(f"Generated {unroll_result.total_equivalents} new equivalents")
        else:
            print("✗ Unrolling failed")

def example_statistics():
    """Example of getting factory statistics."""
    print("\n=== Factory Statistics ===")
    
    config = FactoryConfig(db_path="example_circuits.db")
    factory = IdentityFactory(config)
    
    stats = factory.get_factory_stats()
    
    print("Factory Statistics:")
    print(f"  Total dimension groups: {stats.total_dim_groups}")
    print(f"  Total circuits: {stats.total_circuits}")
    print(f"  Total representatives: {stats.total_representatives}")
    print(f"  Total equivalents: {stats.total_equivalents}")
    print(f"  Generation time: {stats.generation_time:.2f}s")
    print(f"  Unroll time: {stats.unroll_time:.2f}s")

def example_listing_dimension_groups():
    """Example of listing all dimension groups."""
    print("\n=== Listing Dimension Groups ===")
    
    config = FactoryConfig(db_path="example_circuits.db")
    factory = IdentityFactory(config)
    
    # Get all dimension groups
    dim_groups = factory.db.get_all_dim_groups()
    
    if not dim_groups:
        print("No dimension groups found")
        return
    
    print(f"Found {len(dim_groups)} dimension groups:")
    
    for group in dim_groups:
        print(f"  Group {group.id}: ({group.width}, {group.gate_count})")
        print(f"    Circuits: {group.circuit_count}")
        print(f"    Processed: {'Yes' if group.is_processed else 'No'}")
        
        # Get representatives
        representatives = factory.db.get_representatives_for_dim_group(group.id)
        print(f"    Representatives: {len(representatives)}")
        
        # Get equivalents
        equivalents = factory.db.get_all_equivalents_for_dim_group(group.id)
        print(f"    Total equivalents: {len(equivalents)}")

def example_custom_configuration():
    """Example of custom factory configuration."""
    print("\n=== Custom Configuration ===")
    
    # Create a custom configuration
    config = FactoryConfig(
        db_path="custom_circuits.db",
        max_inverse_gates=20,  # Lower limit for faster generation
        max_equivalents=100,   # Smaller limit for testing
        solver="minisat-gh",
        enable_post_processing=False,  # Skip simplification for speed
        enable_unrolling=True,
        enable_debris_analysis=False,
        enable_ml_features=False
    )
    
    factory = IdentityFactory(config)
    
    # Generate with custom settings
    print("Generating with custom settings...")
    result = factory.generate_identity_circuit(
        width=3, 
        gate_count=4, 
        enable_post_processing=False
    )
    
    if result["success"]:
        print("✓ Custom generation successful")
        print(f"  Generation time: {result['total_time']:.2f}s")
        
        # Show the generated circuit details
        seed_result = result["seed_generation"]
        circuit = factory.db.get_circuit(seed_result.circuit_id)
        print(f"  Circuit gates: {len(circuit.gates)}")
        print(f"  Permutation: {circuit.permutation}")
    else:
        print(f"✗ Custom generation failed: {result.get('error')}")

def example_circuit_details():
    """Example of getting detailed circuit information."""
    print("\n=== Circuit Details ===")
    
    config = FactoryConfig(
        db_path="example_circuits.db",
        enable_debris_analysis=False,
        enable_ml_features=False
    )
    
    factory = IdentityFactory(config)
    
    # Generate a circuit
    result = factory.generate_identity_circuit(width=3, gate_count=3)
    
    if result["success"]:
        circuit_id = result["seed_generation"].circuit_id
        
        # Get circuit details
        circuit = factory.db.get_circuit(circuit_id)
        
        print(f"Circuit {circuit_id} details:")
        print(f"  Width: {circuit.width}")
        print(f"  Gate count: {circuit.gate_count}")
        print(f"  Gates: {circuit.gates}")
        print(f"  Permutation: {circuit.permutation}")
        print(f"  Created: {circuit.created_at}")

def main():
    """Run all examples."""
    print("Identity Circuit Factory - Example Usage")
    print("Using Corrected Design Architecture")
    print("=" * 50)
    
    try:
        example_basic_generation()
        example_dimension_group_analysis()
        example_batch_generation()
        example_unrolling()
        example_statistics()
        example_listing_dimension_groups()
        example_custom_configuration()
        example_circuit_details()
        
        print("\n" + "=" * 50)
        print("All examples completed successfully!")
        
    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 