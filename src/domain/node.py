from dataclasses import dataclass

@dataclass
class Node:
    id: str
    is_ground: bool = False
