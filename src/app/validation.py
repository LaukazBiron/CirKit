# src/app/validation.py
from collections import defaultdict
from typing import Iterable

class ValidationError(Exception): ...
class ConnectivityError(ValidationError): ...
class GroundError(ValidationError): ...
class ParameterError(ValidationError): ...
class TopologyError(ValidationError): ...

def validate(nl):
    # 1) Un único GND
    gnds = [nid for nid, n in nl.nodes.items() if n.is_ground]
    if len(gnds) == 0:
        raise GroundError("Falta definir un nodo de tierra (GND).")
    if len(gnds) > 1:
        raise GroundError(f"Hay {len(gnds)} nodos marcados como tierra; debe ser exactamente 1.")

    # 2) Componentes presentes
    if not nl.components:
        raise ValidationError("No hay componentes en el circuito.")

    # 3) Nodos válidos, extremos distintos y parámetros sanos
    for c in nl.components:
        if c.n1 not in nl.nodes or c.n2 not in nl.nodes:
            raise TopologyError(f"{c.id}: terminal conectado a nodo inexistente ({c.n1}/{c.n2}).")
        if c.n1 == c.n2:
            raise TopologyError(f"{c.id}: ambos terminales al mismo nodo ({c.n1}).")
        if getattr(c, "kind", "") == "R":
            R = float(getattr(c, "R", 0))
            if not (R > 0):
                raise ParameterError(f"{c.id}: la resistencia R debe ser > 0 (actual: {R}).")
        if getattr(c, "kind", "") == "V":
            # Fuente ideal puede ser cualquier valor real (incluye 0)
            pass
        if getattr(c, "kind", "") == "D":
            pol = getattr(c, "polarity", "A_to_K")
            if pol not in ("A_to_K", "K_to_A"):
                raise ParameterError(f"{c.id}: polarity inválida: {pol}.")

    # 4) Conectividad (desde GND alcanzamos todos los nodos?)
    _assert_connected(nl, start=gnds[0])

    # 5) Sin ramas colgantes (terminales de componentes no conectan a nada más?) — opcional suave
    #    Permitimos resistencias/fuentes/diodos directos a GND o entre nodos si el grafo general es conexo.

def _assert_connected(nl, start: str):
    adj = defaultdict(set)
    for c in nl.components:
        adj[c.n1].add(c.n2); adj[c.n2].add(c.n1)
    seen = set([start]); stack = [start]
    while stack:
        u = stack.pop()
        for v in adj[u]:
            if v not in seen:
                seen.add(v); stack.append(v)
    missing = set(nl.nodes.keys()) - seen
    if missing:
        raise ConnectivityError("Nodos desconectados del GND: " + ", ".join(sorted(missing)))
