def complexity_walk(gates, n: int):
    """
    Return list[int] – Hamming-distance-from-identity after each gate.
    """
    N = 1 << n
    mapping = list(range(N))
    out = []
    for g in gates:
        if g[0] == "NOT":
            mask = 1 << g[1]
            for i in range(N):
                mapping[i] ^= mask
        elif g[0] == "CNOT":
            c, t = g[1:]
            mask = 1 << t
            for i in range(N):
                if mapping[i] & (1 << c):
                    mapping[i] ^= mask
        else:
            c1, c2, t = g[1:]
            mask = 1 << t
            for i in range(N):
                if (mapping[i] & (1 << c1)) and (mapping[i] & (1 << c2)):
                    mapping[i] ^= mask
        hd = sum((i ^ mapping[i]).bit_count() for i in range(N))
        out.append(hd)
    return out