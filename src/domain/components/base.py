from dataclasses import dataclass
from typing import Literal

ComponentKind = Literal["R", "V", "D"]  # Resistor, VSource, Diode

@dataclass
class Component:
    id: str
    n1: str
    n2: str
    kind: ComponentKind
