# -*- coding: utf-8 -*-
from __future__ import annotations

from datetime import datetime
from typing import Dict, Any, Optional

from reportlab.pdfgen import canvas as rlcanvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader

import base64
import io

PAGE_W, PAGE_H = A4
LM, RM, TM, BM = 42, 42, 36, 42


def _hline(c: rlcanvas.Canvas, x: float, y: float, w: float, col=colors.black, lw: float = 1.0) -> None:
    c.setStrokeColor(col)
    c.setLineWidth(lw)
    c.line(x, y, x + w, y)


def _text(
    c: rlcanvas.Canvas,
    x: float,
    y: float,
    txt: str,
    bold: bool = False,
    size: float = 10,
    col=colors.black,
) -> None:
    c.setFillColor(col)
    c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
    c.drawString(x, y, txt)


def _format_netlist(nl: Dict[str, Any]) -> list[str]:
    out: list[str] = []
    for el in nl.get("elements", []):
        t = el.get("type")
        name = el.get("name", "?")
        a = el.get("a")
        b = el.get("b")
        if t == "R":
            out.append(f"{name} (R) {a} - {b}, R={el.get('value', 0)} Ω")
        elif t == "V":
            out.append(f"{name} (V) {a} - {b}, V={el.get('value', 0)} V")
        elif t == "D":
            out.append(f"{name} (D) {a} - {b}")
    return out


def export_solution_pdf(
    path_pdf: str,
    solution: Dict[str, Any],
    diagram: Optional[Dict[str, Any]] = None,
    png_b64: Optional[str] = None,
) -> str:
    c = rlcanvas.Canvas(path_pdf, pagesize=A4)

    x = LM
    y = PAGE_H - TM

    # Encabezado
    _text(c, x, y, "CirKit Emulation Tool — Reporte de Simulación", bold=True, size=18)
    y -= 18
    _text(c, x, y, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), size=10)
    y -= 16

    # Diagrama
    _text(c, x, y, "Diagrama del circuito:", bold=True, size=12)
    y -= 8

    box_w, box_h = 500.0, 320.0
    box_x = (PAGE_W - box_w) / 2.0
    box_y = y - box_h - 6.0

    c.setStrokeColor(colors.black)
    c.setLineWidth(1.0)
    c.rect(box_x, box_y, box_w, box_h, stroke=1, fill=0)

    if png_b64:
        try:
            raw = base64.b64decode(png_b64)
            img = ImageReader(io.BytesIO(raw))
            iw, ih = img.getSize()

            scale = min((box_w - 10.0) / iw, (box_h - 10.0) / ih)
            draw_w = iw * scale
            draw_h = ih * scale
            draw_x = box_x + (box_w - draw_w) / 2.0
            draw_y = box_y + (box_h - draw_h) / 2.0

            c.drawImage(
                img, draw_x, draw_y, width=draw_w, height=draw_h,
                preserveAspectRatio=True, mask="auto",
            )
        except Exception as e:
            _text(c, box_x + 10, box_y + box_h / 2.0, f"Error al mostrar imagen: {e}", col=colors.red)
    else:
        _text(c, box_x + 10, box_y + box_h / 2.0, "No se recibió imagen del circuito.", col=colors.gray)

    y = box_y - 24.0
    _hline(c, x, y, PAGE_W - LM - RM, lw=0.7)
    y -= 14.0

    # Componentes (desde netlist)
    _text(c, x, y, "Componentes / Netlist:", bold=True, size=12)
    y -= 14.0

    nl_dict = solution.get("netlist")
    if isinstance(nl_dict, dict):
        for line in _format_netlist(nl_dict):
            _text(c, x, y, line, size=9)
            y -= 12.0
    else:
        _text(c, x, y, "No disponible.", size=9)
        y -= 12.0

    y -= 8.0
    _hline(c, x, y, PAGE_W - LM - RM, lw=0.7)
    y -= 14.0

    # Voltajes
    _text(c, x, y, "Voltajes nodales (ref. a GND):", bold=True, size=12)
    y -= 14.0
    nodes = solution.get("node_voltages", {})
    if nodes:
        for n, v in nodes.items():
            _text(c, x, y, f"{n}: {v:.6f} V", size=9)
            y -= 12.0
    else:
        _text(c, x, y, "—", size=9)
        y -= 12.0

    y -= 6.0
    _hline(c, x, y, PAGE_W - LM - RM, lw=0.7)
    y -= 14.0

    # Corrientes
    _text(c, x, y, "Corrientes de ramas:", bold=True, size=12)
    y -= 14.0
    currents = solution.get("branch_currents", {})
    if currents:
        for name, a in currents.items():
            _text(c, x, y, f"{name}: {a:.9f} A", size=9)
            y -= 12.0
    else:
        _text(c, x, y, "—", size=9)
        y -= 12.0

    y -= 6.0
    _hline(c, x, y, PAGE_W - LM - RM, lw=0.7)
    y -= 14.0

    # Verificación de leyes
    _text(c, x, y, "Verificación de leyes:", bold=True, size=12)
    y -= 14.0

    kcl = solution.get("kcl", {})
    kvl = solution.get("kvl", {})

    _text(c, x, y, "• LCK (KCL):", size=9)
    y -= 12.0
    if kcl:
        for node, ok in kcl.items():
            _text(c, x, y, f"  {node}: {'OK' if ok else 'FAIL'}", size=9)
            y -= 12.0
    else:
        _text(c, x, y, "  —", size=9)
        y -= 12.0

    y -= 6.0
    _text(c, x, y, "• LVK (KVL):", size=9)
    y -= 12.0
    if kvl:
        for loop_name, ok in kvl.items():
            _text(c, x, y, f"  {loop_name}: {'OK' if ok else 'FAIL'}", size=9)
            y -= 12.0
    else:
        _text(c, x, y, "  —", size=9)
        y -= 12.0

    c.showPage()
    c.save()
    return path_pdf
