from dataclasses import dataclass, field
from typing import Dict, List
from .node import Node
from .components.base import Component

@dataclass
class Netlist:
    nodes: Dict[str, Node] = field(default_factory=dict)
    components: List[Component] = field(default_factory=list)

    def add_node(self, id: str, is_ground: bool = False) -> Node:
        if id not in self.nodes:
            self.nodes[id] = Node(id=id, is_ground=is_ground)
        else:
            # si ya existe, solo actualiza is_ground si es True
            self.nodes[id].is_ground = self.nodes[id].is_ground or is_ground
        return self.nodes[id]

    def add_component(self, c: Component) -> None:
        self.components.append(c)

    def ground_id(self) -> str:
        for k, n in self.nodes.items():
            if n.is_ground:
                return k
        raise ValueError("Falta nodo de tierra (GND).")
