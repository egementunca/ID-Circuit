from itertools import product
from collections import defaultdict
from sat_revsynth.circuit.circuit import Circuit
import os

def normalize_gate(gate):
    """Normalize gates to canonical form - sort control qubits for CCX gates"""
    if gate[0] == 'CCX':
        control1, control2, target = gate[1], gate[2], gate[3]
        # Sort the control qubits to get canonical form
        controls = sorted([control1, control2])
        return ('CCX', controls[0], controls[1], target)
    else:
        return gate

def get_possible_gates(width):
    """Get all possible gates for a given circuit width"""
    gates = []
    
    # X gates on each qubit
    for i in range(width):
        gates.append(('X', i))
    
    # CX gates (all possible control/target combinations)
    for control in range(width):
        for target in range(width):
            if control != target:
                gates.append(('CX', control, target))
    
    # CCX gates (Toffoli) for 3+ qubits - normalize to avoid duplicates
    if width >= 3:
        ccx_gates = set()  # Use set to avoid duplicates
        for control1 in range(width):
            for control2 in range(width):
                for target in range(width):
                    if len(set([control1, control2, target])) == 3:  # All different
                        # Normalize by sorting controls
                        controls = sorted([control1, control2])
                        normalized_gate = ('CCX', controls[0], controls[1], target)
                        ccx_gates.add(normalized_gate)
        gates.extend(list(ccx_gates))
    
    return gates

def apply_gate_classical(state, gate):
    """Apply a gate to an n-qubit computational basis state classically"""
    # state is a tuple of bits (q0, q1, q2, ...)
    state_list = list(state)
    
    if gate[0] == 'X':
        qubit = gate[1]
        state_list[qubit] = 1 - state_list[qubit]  # Flip the qubit
    
    elif gate[0] == 'CX':
        control, target = gate[1], gate[2]
        if state_list[control] == 1:  # If control is |1⟩, flip target
            state_list[target] = 1 - state_list[target]
    
    elif gate[0] == 'CCX':
        control1, control2, target = gate[1], gate[2], gate[3]
        if state_list[control1] == 1 and state_list[control2] == 1:  # Both controls are |1⟩
            state_list[target] = 1 - state_list[target]
    
    return tuple(state_list)

def simulate_circuit_classical(gate_sequence, width):
    """Simulate a gate sequence on all computational basis states"""
    # Generate all 2^width computational basis states
    basis_states = []
    for i in range(2**width):
        state = tuple((i >> j) & 1 for j in range(width))
        basis_states.append(state)
    
    results = {}
    for initial_state in basis_states:
        current_state = initial_state
        for gate in gate_sequence:
            current_state = apply_gate_classical(current_state, gate)
        results[initial_state] = current_state
    
    return results

def is_identity_classical(gate_sequence, width):
    """Check if a gate sequence implements identity using classical simulation"""
    results = simulate_circuit_classical(gate_sequence, width)
    
    # For identity, each basis state should map to itself
    for initial_state, final_state in results.items():
        if initial_state != final_state:
            return False
    return True

def normalize_circuit(gate_sequence):
    """Normalize a circuit by normalizing all gates"""
    return tuple(normalize_gate(gate) for gate in gate_sequence)

def circuits_are_equivalent(circuit1, circuit2):
    """Check if two circuits are equivalent after normalization"""
    return normalize_circuit(circuit1) == normalize_circuit(circuit2)

def filter_equivalent_circuits(circuits):
    """Remove equivalent circuits, keeping only unique normalized forms"""
    unique_circuits = []
    seen_normalized = set()
    
    for circuit in circuits:
        normalized = normalize_circuit(circuit)
        if normalized not in seen_normalized:
            seen_normalized.add(normalized)
            unique_circuits.append(circuit)
    
    return unique_circuits

def create_circuit_visualization(gate_sequence, width):
    """Create a Circuit with proper sequential visualization"""
    circuit = Circuit(width)
    
    for gate in gate_sequence:
        if gate[0] == 'X':
            circuit.x(gate[1])
        elif gate[0] == 'CX':
            circuit.cx(gate[1], gate[2])
        elif gate[0] == 'CCX':
            circuit.mcx([gate[1], gate[2]], gate[3])
    
    return circuit

def count_gates_simple(gate_sequence):
    """Count total gates by type, ignoring specific qubits/directions"""
    counts = {'X': 0, 'CX': 0, 'CCX': 0}
    
    for gate in gate_sequence:
        if gate[0] in counts:
            counts[gate[0]] += 1
    
    return counts

def generate_identity_circuits(width, length, output_folder="identity_circuits_analysis"):
    """Generate all identity circuits for given width and length"""
    
    print(f"Searching for all {width}-qubit, {length}-gate identity circuits...")
    print("=" * 60)
    
    # Get all possible gates for this width
    gates = get_possible_gates(width)
    total_combinations = len(gates)**length
    print(f"Available gate types: {set(gate[0] for gate in gates)}")
    print(f"Total gate options: {len(gates)}")
    print(f"Total combinations to check: {total_combinations}")
    
    # Early warning for very large computations
    if total_combinations > 1000000:
        print(f"⚠️  WARNING: This will check {total_combinations:,} combinations - may take significant time!")
    
    identity_circuits = []
    
    # Try all possible combinations
    total_combinations_checked = 0
    for sequence in product(gates, repeat=length):
        total_combinations_checked += 1
        if total_combinations_checked % 100000 == 0:  # Progress indicator for large searches
            print(f"Checked {total_combinations_checked:,} combinations...")
        
        if is_identity_classical(sequence, width):
            identity_circuits.append(sequence)
    
    print(f"Found {len(identity_circuits)} identity circuits before filtering")
    
    # Filter out equivalent circuits
    identity_circuits = filter_equivalent_circuits(identity_circuits)
    print(f"Found {len(identity_circuits)} unique identity circuits after removing equivalents")
    
    if len(identity_circuits) == 0:
        print("No identity circuits found!")
        return 0
    
    # Group circuits by gate counts
    grouped_circuits = defaultdict(list)
    for sequence in identity_circuits:
        counts = count_gates_simple(sequence)
        # Create a tuple key for grouping
        key = (counts['X'], counts['CX'], counts['CCX'])
        grouped_circuits[key].append(sequence)
    
    # Sort groups by the key for consistent ordering
    sorted_groups = sorted(grouped_circuits.items())
    
    print(f"Grouped into {len(sorted_groups)} different gate count patterns")
    
    # Create output filename
    filename = f"identity_circuits_{width}w_{length}l.txt"
    filepath = os.path.join(output_folder, filename)
    
    print(f"Writing results to '{filepath}'...")
    
    # Ensure output directory exists
    os.makedirs(output_folder, exist_ok=True)
    
    # Write results to file
    with open(filepath, 'w') as f:
        f.write(f"{width}-Qubit, {length}-Gate Identity Circuits - Grouped by Total Gate Counts\n")
        f.write("(Using correct sequential gate visualization - equivalent circuits filtered)\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total unique circuits found: {len(identity_circuits)}\n")
        f.write(f"Number of different gate count patterns: {len(sorted_groups)}\n")
        f.write(f"Available gates: {set(gate[0] for gate in gates)}\n")
        if width >= 3:
            f.write("Note: CCX gates are normalized (controls sorted) to avoid counting equivalent circuits\n")
        f.write("\n")
        
        for group_num, (gate_counts, circuits) in enumerate(sorted_groups, 1):
            x_total, cx_total, ccx_total = gate_counts
            f.write(f"GROUP {group_num}: X gates = {x_total}, CX gates = {cx_total}")
            if width >= 3:
                f.write(f", CCX gates = {ccx_total}")
            f.write(f"\nCircuits in this group: {len(circuits)}\n")
            f.write("-" * 50 + "\n")
            
            for circuit_num, sequence in enumerate(circuits, 1):
                f.write(f"\nCircuit {group_num}.{circuit_num}:\n")
                f.write(f"Gate sequence: {sequence}\n")
                if width >= 3:
                    f.write(f"Normalized: {normalize_circuit(sequence)}\n")
                
                # Create and write correct ASCII representation
                try:
                    circuit = create_circuit_visualization(sequence, width)
                    f.write(str(circuit) + "\n")
                except Exception as e:
                    f.write(f"[Visualization error: {e}]\n")
                f.write("-" * 30 + "\n")
            
            f.write("\n" + "=" * 80 + "\n\n")
    
    print(f"Results saved to '{filepath}'")
    
    # Print summary to console
    print(f"\nSUMMARY BY TOTAL GATE COUNTS:")
    print("-" * 50)
    for group_num, (gate_counts, circuits) in enumerate(sorted_groups, 1):
        x_total, cx_total, ccx_total = gate_counts
        summary = f"Group {group_num}: {x_total} X, {cx_total} CX"
        if width >= 3:
            summary += f", {ccx_total} CCX"
        summary += f" - {len(circuits)} circuits"
        print(summary)
    
    print(f"\nTotal: {len(identity_circuits)} unique circuits in {len(sorted_groups)} groups")
    return len(identity_circuits)

def main():
    """Generate identity circuits for all requested configurations"""
    # All combinations of widths 2-4 and lengths 1-4
    configurations = []
    for width in [2, 3, 4]:
        for length in [1, 2, 3, 4]:
            configurations.append((width, length))
    
    results = {}
    total_configs = len(configurations)
    
    print(f"🚀 COMPREHENSIVE IDENTITY CIRCUIT ANALYSIS")
    print(f"Will process {total_configs} configurations: widths 2-4, lengths 1-4")
    print(f"{'='*80}")
    
    for config_num, (width, length) in enumerate(configurations, 1):
        print(f"\n{'='*80}")
        print(f"PROCESSING CONFIGURATION {config_num}/{total_configs}: {width}-QUBIT, {length}-GATE")
        print(f"{'='*80}")
        
        try:
            count = generate_identity_circuits(width, length)
            results[(width, length)] = count
            print(f"✅ Completed {width}x{length}: {count} unique circuits")
        except Exception as e:
            print(f"❌ Error in {width}x{length}: {e}")
            results[(width, length)] = "ERROR"
        
        print(f"\nProgress: {config_num}/{total_configs} configurations completed\n")
    
    # Create comprehensive summary
    print(f"\n{'='*80}")
    print("🎯 FINAL COMPREHENSIVE SUMMARY")
    print(f"{'='*80}")
    
    # Print results in a nice table format
    print(f"{'Width/Length':<12} {'1-gate':<8} {'2-gate':<8} {'3-gate':<8} {'4-gate':<8}")
    print("-" * 50)
    
    for width in [2, 3, 4]:
        row = f"{width}-qubit"
        for length in [1, 2, 3, 4]:
            count = results.get((width, length), "N/A")
            if isinstance(count, int):
                row += f"{count:<8}"
            else:
                row += f"{str(count):<8}"
        print(row)
    
    print(f"\n📁 All files saved in 'identity_circuits_analysis/' folder")
    
    # Calculate some interesting statistics
    print(f"\n📊 STATISTICS:")
    total_circuits = sum(count for count in results.values() if isinstance(count, int))
    print(f"Total unique identity circuits found: {total_circuits:,}")
    
    # Find most complex configuration
    max_count = max((count for count in results.values() if isinstance(count, int)), default=0)
    max_configs = [(w, l) for (w, l), count in results.items() if count == max_count]
    if max_configs:
        print(f"Most complex configuration: {max_configs[0][0]}x{max_configs[0][1]} with {max_count:,} circuits")

if __name__ == "__main__":
    main() 