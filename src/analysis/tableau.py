import numpy as np
from typing import Tuple
from ..domain.netlist import Netlist
from ..domain.components.resistor import Resistor
from ..domain.components.vsource import VSource


class Meta:
    """
    Guarda metadatos de simulación: índices de nodos, componentes, etc.
    """
    def __init__(self, node_index, components):
        self.node_index = node_index
        self.components = components

    def reconstruct_solution(self, x):
        """
        Reconstruye un objeto Solution con voltajes e intensidades.
        """
        from .results import Solution

        V = {nid: float(x[idx]) for nid, idx in self.node_index.items()}
        I = {}

        def v(nid):
            return V.get(nid, 0.0)  # GND = 0

        for c in self.components:
            if isinstance(c, Resistor):
                I[c.id] = (v(c.n1) - v(c.n2)) / c.R
            elif isinstance(c, VSource):
                # Estimación simple (corriente positiva de n1 → n2)
                I[c.id] = 0.0

        return Solution(node_voltages=V, branch_currents=I, diode_states={}, checks={})


def build_system(nl: Netlist) -> Tuple[np.ndarray, np.ndarray, Meta]:
    """
    Construye la matriz de ecuaciones A·x = b mediante el método de nodos.
    - Aplica LVK y LCK.
    - Considera resistencias y fuentes de voltaje ideal con terminal a GND.
    """

    # Nodos (sin GND)
    nodes = [nid for nid, n in nl.nodes.items() if not n.is_ground]
    node_index = {nid: i for i, nid in enumerate(nodes)}

    # Matriz de conductancias G y vector de corriente equivalente I
    n = len(nodes)
    G = np.zeros((n, n), dtype=float)
    I = np.zeros(n, dtype=float)

    # --- Resistores (Ley de Ohm + KCL)
    for c in nl.components:
        if isinstance(c, Resistor):
            g = 1.0 / c.R
            if c.n1 not in nl.nodes or c.n2 not in nl.nodes:
                continue

            n1, n2 = c.n1, c.n2
            if not nl.nodes[n1].is_ground:
                G[node_index[n1], node_index[n1]] += g
            if not nl.nodes[n2].is_ground:
                G[node_index[n2], node_index[n2]] += g

            if not nl.nodes[n1].is_ground and not nl.nodes[n2].is_ground:
                G[node_index[n1], node_index[n2]] -= g
                G[node_index[n2], node_index[n1]] -= g

    # --- Fuentes de voltaje (aplicadas respecto a GND)
    for c in nl.components:
        if isinstance(c, VSource):
            # Solo soporta fuentes a GND (n2 = GND o n1 = GND)
            if nl.nodes[c.n1].is_ground and not nl.nodes[c.n2].is_ground:
                # V entre GND → n2 = -V
                I[node_index[c.n2]] -= 1e12 * c.V
                G[node_index[c.n2], node_index[c.n2]] += 1e12
            elif nl.nodes[c.n2].is_ground and not nl.nodes[c.n1].is_ground:
                # V entre n1 → GND = +V
                I[node_index[c.n1]] += 1e12 * c.V
                G[node_index[c.n1], node_index[c.n1]] += 1e12
            else:
                # Si ninguna terminal está a GND, ignoramos por ahora (MVP)
                pass

    # Resultado
    A = G
    b = I
    return A, b, Meta(node_index=node_index, components=list(nl.components))
