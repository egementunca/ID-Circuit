# sat_revsynth_inverse.py  (replace earlier helper)
from truth_table.truth_table import TruthTable
from synthesizers.optimal_synthesizer import OptimalSynthesizer
from sat.solver import Solver

def inverse_sat(forward_perm, n, max_gc=40, solver_name="minisat-gh"):
    # 1) inverse permutation --------------------------------------------
    inv = [0]*(1 << n)
    for x, y in enumerate(forward_perm):
        inv[y] = x

    # 2) SAT synthesis ---------------------------------------------------
    # Exclude exact gate matches / (add id template extension by unrolling / smaller circuits may be finding templates within first P?) 
    net = OptimalSynthesizer(
            TruthTable(n, inv),
            0, max_gc,
            Solver(solver_name)
          ).solve()
    if net is None:
        raise RuntimeError("SAT solver found no inverse ≤ max_gc")

    # 3) normalise every gate -------------------------------------------
    out = []
    for g in net:
        # --- old textual tags ('cx',…), keep previous handling ----------
        if isinstance(g, tuple) and isinstance(g[0], str):
            tag = g[0]
            if tag in ("x", "NOT"):
                out.append(("NOT", g[1]))
            elif tag in ("cx", "CNOT"):
                _, c, t = g
                out.append(("CNOT", c, t))
            elif tag in ("ccx", "TOFFOLI"):
                _, c1, c2, t = g
                out.append(("TOFFOLI", c1, c2, t))
            else:
                raise ValueError(f"unrecognised textual tag {tag!r}")

        # --- canonical “controls, target” pair --------------------------
        elif (isinstance(g, (list, tuple)) and len(g) == 2 and
              isinstance(g[1], int)):

            controls, target = g
            # make sure we have a list of controls
            if not isinstance(controls, (list, tuple)):
                controls = [controls]

            if len(controls) == 0:
                out.append(("NOT", target))
            elif len(controls) == 1:
                out.append(("CNOT", controls[0], target))
            elif len(controls) == 2:
                out.append(("TOFFOLI", controls[0], controls[1], target))
            else:
                raise ValueError("controls >2 not supported (NCT library)")

        else:
            raise TypeError(f"unexpected gate encoding {g!r}")

    return out   # list of ('NOT',q) / ('CNOT',c,t) / ('TOFFOLI',c1,c2,t)