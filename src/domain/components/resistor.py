from dataclasses import dataclass
from .base import Component

@dataclass
class Resistor(Component):
    R: float = 1.0
    def __init__(self, id: str, n1: str, n2: str, R: float):
        super().__init__(id, n1, n2, "R")
        self.R = float(R)
