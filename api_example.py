#!/usr/bin/env python3
"""
Example usage of the Identity Circuit Factory API.

This script demonstrates how to use the API client to interact with
the factory server for generating, unrolling, and managing circuits.
"""

import asyncio
import json
from pathlib import Path

# Add the current directory to the path so we can import our modules
import sys
sys.path.insert(0, str(Path(__file__).parent))

from identity_factory.api.client import IdentityFactoryClient, IdentityFactoryClientSync
from identity_factory.api.models import *

async def example_async_client():
    """Example using the async API client."""
    print("=== Async API Client Example ===")
    
    # Create async client
    async with IdentityFactoryClient(base_url="http://localhost:8000") as client:
        
        # Check health
        print("Checking API health...")
        health = await client.health_check()
        print(f"API Status: {health.status}")
        print(f"Database Connected: {health.database_connected}")
        print(f"SAT Solver Available: {health.sat_solver_available}")
        
        # Get statistics
        print("\nGetting factory statistics...")
        stats = await client.get_stats()
        print(f"Total Dimension Groups: {stats.total_dim_groups}")
        print(f"Total Circuits: {stats.total_circuits}")
        print(f"Total Seeds Generated: {stats.total_seeds_generated}")
        
        # Generate a circuit
        print("\nGenerating identity circuit...")
        request = CircuitRequest(
            width=3,
            length=5,
            max_inverse_gates=30,
            enable_unrolling=True,
            enable_post_processing=True
        )
        
        result = await client.generate_circuit(request)
        print(f"Generation Success: {result.success}")
        if result.success:
            print(f"Seed Circuit ID: {result.seed_circuit_id}")
            print(f"Dimension Group ID: {result.dim_group_id}")
            print(f"Total Equivalents: {result.total_equivalents}")
            print(f"Generation Time: {result.total_time:.2f}s")
        
        # Get dimension groups
        print("\nGetting dimension groups...")
        dim_groups = await client.get_dimension_groups()
        print(f"Found {len(dim_groups)} dimension groups:")
        
        for dg in dim_groups[:5]:  # Show first 5
            print(f"  ({dg.width}, {dg.length}): {dg.total_equivalents} circuits")
        
        # Get recommendations
        print("\nGetting recommendations...")
        recommendations = await client.get_recommendations(target_width=4, max_length=10, limit=5)
        print(f"Recommended dimensions for width 4:")
        for width, length in recommendations:
            print(f"  ({width}, {length})")

def example_sync_client():
    """Example using the synchronous API client."""
    print("\n=== Synchronous API Client Example ===")
    
    # Create sync client
    with IdentityFactoryClientSync(base_url="http://localhost:8000") as client:
        
        # Check health
        print("Checking API health...")
        health = client.health_check()
        print(f"API Status: {health.status}")
        
        # Get detailed statistics
        print("\nGetting detailed statistics...")
        detailed_stats = client.get_detailed_stats()
        print(f"Factory Stats: {detailed_stats.factory_stats.total_dim_groups} groups")
        print(f"Seed Stats: {detailed_stats.seed_stats.get('total_dim_groups', 0)} groups")
        print(f"Unroll Stats: {detailed_stats.unroll_stats.get('total_circuits', 0)} circuits")
        
        # Generate circuits in batch
        print("\nGenerating circuits in batch...")
        batch_request = BatchCircuitRequest(
            dimensions=[(3, 4), (3, 5), (4, 4)],
            max_inverse_gates=25,
            enable_unrolling=True,
            enable_post_processing=False  # Skip for speed
        )
        
        results = client.generate_circuits_batch(batch_request)
        print(f"Batch generation results:")
        for key, result in results.items():
            status = "✓ Success" if result.success else "✗ Failed"
            print(f"  {key}: {status}")
            if result.success:
                print(f"    Circuit ID: {result.seed_circuit_id}")
                print(f"    Time: {result.total_time:.2f}s")
        
        # Unroll a dimension group
        if results:
            # Get the first successful result
            first_success = next((r for r in results.values() if r.success), None)
            if first_success and first_success.dim_group_id:
                print(f"\nUnrolling dimension group {first_success.dim_group_id}...")
                unroll_request = UnrollRequest(
                    dim_group_id=first_success.dim_group_id,
                    unroll_types=[UnrollType.SWAP, UnrollType.ROTATION],
                    max_equivalents=100
                )
                
                unroll_result = client.unroll_dimension_group(unroll_request)
                print(f"Unrolling Success: {unroll_result.success}")
                if unroll_result.success:
                    print(f"Total Equivalents: {unroll_result.total_equivalents}")
                    print(f"New Circuits: {unroll_result.new_circuits}")
                    print(f"Unroll Types: {unroll_result.unroll_types}")

async def example_advanced_operations():
    """Example of advanced API operations."""
    print("\n=== Advanced API Operations ===")
    
    async with IdentityFactoryClient(base_url="http://localhost:8000") as client:
        
        # Get circuits with pagination and filtering
        print("Getting circuits with pagination...")
        circuits_page = await client.get_circuits(
            page=1,
            size=10,
            sort_by="width",
            sort_order="asc"
        )
        print(f"Page {circuits_page.page} of {circuits_page.pages}")
        print(f"Total circuits: {circuits_page.total}")
        
        # Get specific dimension group
        dim_groups = await client.get_dimension_groups()
        if dim_groups:
            target_group = dim_groups[0]
            print(f"\nGetting circuits in dimension group {target_group.id}...")
            
            circuits = await client.get_circuits_in_dimension_group(target_group.id)
            print(f"Found {len(circuits)} circuits in group")
            
            if circuits:
                # Get specific circuit details
                circuit = circuits[0]
                print(f"\nCircuit {circuit.id} details:")
                print(f"  Width: {circuit.width}")
                print(f"  Length: {circuit.length}")
                print(f"  Gates: {len(circuit.gates)}")
                print(f"  Complexity Walk: {len(circuit.complexity_walk) if circuit.complexity_walk else 0} steps")
        
        # Export/Import example
        if dim_groups:
            print(f"\nExporting dimension group {dim_groups[0].id}...")
            export_request = ExportRequest(
                dim_group_id=dim_groups[0].id,
                include_circuits=True,
                include_equivalents=True,
                include_simplifications=True
            )
            
            try:
                export_data = await client.export_dimension_group(export_request)
                print(f"Export successful: {len(export_data)} bytes")
                
                # Save to file
                export_file = f"export_group_{dim_groups[0].id}.json"
                with open(export_file, 'wb') as f:
                    f.write(export_data)
                print(f"Export saved to {export_file}")
                
            except Exception as e:
                print(f"Export failed: {e}")

def example_error_handling():
    """Example of error handling with the API client."""
    print("\n=== Error Handling Example ===")
    
    with IdentityFactoryClientSync(base_url="http://localhost:8000") as client:
        
        try:
            # Try to get a non-existent circuit
            print("Trying to get non-existent circuit...")
            circuit = client.get_circuit(99999)
            print("Unexpected success!")
            
        except Exception as e:
            print(f"Expected error: {type(e).__name__}: {e}")
        
        try:
            # Try to generate with invalid parameters
            print("\nTrying to generate with invalid parameters...")
            request = CircuitRequest(
                width=15,  # Too large
                length=100,  # Too large
                max_inverse_gates=200  # Too large
            )
            result = client.generate_circuit(request)
            print("Unexpected success!")
            
        except Exception as e:
            print(f"Expected error: {type(e).__name__}: {e}")

async def main():
    """Run all API examples."""
    print("Identity Circuit Factory API - Example Usage")
    print("=" * 60)
    
    try:
        # Run async examples
        await example_async_client()
        
        # Run sync examples
        example_sync_client()
        
        # Run advanced examples
        await example_advanced_operations()
        
        # Run error handling examples
        example_error_handling()
        
        print("\n" + "=" * 60)
        print("All API examples completed successfully!")
        
    except Exception as e:
        print(f"\nError running API examples: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main()) 