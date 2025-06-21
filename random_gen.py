import random

def random_circuit(n: int, L: int, one_gate_per_time_step: bool = True):
    """
    Return (gates, permutation) where
      gates        : list of ('NOT',q) / ('CNOT',c,t) / ('TOFFOLI',c1,c2,t)
      permutation  : length 2**n list, mapping input→output
    """
    assert 3 <= n <= 9
    gates = []

    if one_gate_per_time_step:
        for _ in range(L):
            typ = random.choice(["NOT", "CNOT", "TOFFOLI"])
            if typ == "NOT":
                gates.append(("NOT", random.randrange(n)))
            elif typ == "CNOT":
                ctrl, tgt = random.sample(range(n), 2)
                gates.append(("CNOT", ctrl, tgt))
            else:
                c1, c2, t = random.sample(range(n), 3)
                gates.append(("TOFFOLI", c1, c2, t))
    else:
        remaining = L
        while remaining:
            free = set(range(n))
            while remaining and free:
                typ = random.choice(
                    [g for g, need in
                     [("TOFFOLI", 3), ("CNOT", 2), ("NOT", 1)]
                     if len(free) >= need]
                )
                if typ == "NOT":
                    q = random.choice(tuple(free))
                    gates.append(("NOT", q))
                    free.remove(q)
                elif typ == "CNOT":
                    c, t = random.sample(tuple(free), 2)
                    gates.append(("CNOT", c, t))
                    free.difference_update({c, t})
                else:
                    c1, c2, t = random.sample(tuple(free), 3)
                    gates.append(("TOFFOLI", c1, c2, t))
                    free.difference_update({c1, c2, t})
                remaining -= 1
                if random.random() < 0.3:
                    break

    # simulate to get permutation
    N = 1 << n
    perm = list(range(N))
    for g in gates:
        if g[0] == "NOT":
            mask = 1 << g[1]
            for i in range(N):
                perm[i] ^= mask
        elif g[0] == "CNOT":
            c, t = g[1:]
            mask = 1 << t
            for i in range(N):
                if perm[i] & (1 << c):
                    perm[i] ^= mask
        else:
            c1, c2, t = g[1:]
            mask = 1 << t
            for i in range(N):
                if (perm[i] & (1 << c1)) and (perm[i] & (1 << c2)):
                    perm[i] ^= mask
    return gates, perm