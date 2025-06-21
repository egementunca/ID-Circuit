from qiskit import QuantumCircuit

def gates_to_qc_strict(gates, n):
    """
    Build a QuantumCircuit that preserves the *exact* left-to-right order
    you supply.  Every gate is followed by a full-width barrier so no
    automatic column merging can occur.
    """
    qc = QuantumCircuit(n, name="strict")

    for g in gates:
        # --- append the gate in whichever encoding ---------------
        if isinstance(g[0], list):          # sat_revsynth ([ctrls], tgt)
            ctrls, tgt = g
            if   len(ctrls) == 0: qc.x(tgt)
            elif len(ctrls) == 1: qc.cx(ctrls[0], tgt)
            else:                  qc.ccx(ctrls[0], ctrls[1], tgt)
        else:                                # canonical ('NOT', …)
            typ = g[0]
            if typ == "NOT":
                qc.x(g[1])
            elif typ == "CNOT":
                qc.cx(g[1], g[2])
            elif typ == "TOFFOLI":
                qc.ccx(g[1], g[2], g[3])
            else:
                raise ValueError(f"unknown tag {typ}")

        # --- freeze this column ---------------------------------
        qc.barrier(*range(n))      # full-width barrier

    return qc


def draw_gate_list_strict(gates, n, style="mpl", idle_wires=False, **kw):
    """
    Draw the circuit *exactly* as specified: one column per gate,
    no automatic justification.
    """
    qc = gates_to_qc_strict(gates, n)
    return qc.draw(style=style, idle_wires=idle_wires,
                   justify="none", fold=-1, **kw)
