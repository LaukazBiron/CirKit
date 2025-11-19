from dataclasses import dataclass
from .base import Component

@dataclass
class IdealDiode(Component):
    polarity: str = "A_to_K"  # ánodo -> cátodo
    def __init__(self, id: str, n1: str, n2: str, polarity: str = "A_to_K"):
        super().__init__(id, n1, n2, "D")
        self.polarity = polarity
