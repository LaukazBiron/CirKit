import json
from typing import Any
from ..domain.netlist import Netlist
from ..domain.components.resistor import Resistor
from ..domain.components.vsource import VSource
from ..domain.components.diode import IdealDiode

def load_json(path: str) -> Netlist:
    data = json.load(open(path, "r", encoding="utf-8"))
    nl = Netlist()
    for n in data["nodes"]:
        nl.add_node(n["id"], n.get("is_ground", False))
    for c in data["components"]:
        if c["kind"] == "R":
            nl.add_component(Resistor(c["id"], c["n1"], c["n2"], c["R"]))
        elif c["kind"] == "V":
            nl.add_component(VSource(c["id"], c["n1"], c["n2"], c["V"]))
        elif c["kind"] == "D":
            nl.add_component(IdealDiode(c["id"], c["n1"], c["n2"], c.get("polarity","A_to_K")))
    return nl

def save_json(nl: Netlist, path: str) -> None:
    out: dict[str, Any] = {
        "nodes": [{"id": n.id, "is_ground": n.is_ground} for n in nl.nodes.values()],
        "components": []
    }
    for c in nl.components:
        item = {"id": c.id, "kind": c.kind, "n1": c.n1, "n2": c.n2}
        if c.kind == "R": item["R"] = c.R
        if c.kind == "V": item["V"] = c.V
        if c.kind == "D": item["polarity"] = c.polarity
        out["components"].append(item)
    json.dump(out, open(path, "w", encoding="utf-8"), indent=2)
