from dataclasses import dataclass, field

@dataclass
class Solution:
    node_voltages: dict[str, float] = field(default_factory=dict)
    branch_currents: dict[str, float] = field(default_factory=dict)
    diode_states: dict[str, str] = field(default_factory=dict)
    checks: dict[str, dict] = field(default_factory=dict)
