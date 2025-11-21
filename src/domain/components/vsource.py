from dataclasses import dataclass
from .base import Component

@dataclass
class VSource(Component):
    V: float = 0.0
    def __init__(self, id: str, n1: str, n2: str, V: float):
        super().__init__(id, n1, n2, "V")
        self.V = float(V)
