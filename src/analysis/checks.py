def run_checks(nl, sol, rtol=1e-6, atol=1e-9):
    V = sol.node_voltages
    def v(n): return V.get(n, 0.0)
    kcl = {}
    for nid, node in nl.nodes.items():
        if node.is_ground: continue
        s = 0.0
        for c in nl.components:
            if getattr(c, "kind", "") == "R":
                if c.n1 == nid:
                    s += (v(c.n1)-v(c.n2))/c.R
                elif c.n2 == nid:
                    s -= (v(c.n1)-v(c.n2))/c.R
        kcl[nid] = {"sum_A": s, "ok": abs(s) <= max(atol, rtol*max(1.0, abs(s)))}
    kvl = {}
    for c in nl.components:
        if getattr(c, "kind", "") == "V":
            err = (v(c.n1) - v(c.n2)) - c.V
            kvl[f"KVL_{c.id}"] = {"sum_V": err, "ok": abs(err) <= 1e-6}
    return {"KCL": kcl, "KVL": kvl}
