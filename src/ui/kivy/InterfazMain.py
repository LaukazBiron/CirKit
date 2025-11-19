# -*- coding: utf-8 -*-
# pyright: reportOptionalMemberAccess=false, reportAttributeAccessIssue=false
import os, sys, json, math, pathlib, time, heapq, base64, tempfile
from dataclasses import dataclass
from typing import Dict, Tuple, List, Optional, Any

# -------------------------------------------------
#  RUTAS DE PROYECTO
# -------------------------------------------------
ROOT = pathlib.Path(__file__).resolve().parents[3]
SRC  = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# -------------------------------------------------
#  KIVY
# -------------------------------------------------
import kivy
kivy.require("2.3.0")

from kivy.app import App
from kivy.lang import Builder
from kivy.clock import Clock
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, DictProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.resources import resource_add_path
from kivy.graphics import (
    Color, Line, Rectangle, Ellipse, Triangle,
    PushMatrix, PopMatrix, Rotate, Translate, InstructionGroup
)

# -------------------------------------------------
#  DIALOGO NATIVO (tk)
# -------------------------------------------------
import tkinter as tk
from tkinter import filedialog

# -------------------------------------------------
#  BACKEND
# -------------------------------------------------
from src.app.simulate import simulate
from src.app.export_pdf import export_solution_pdf
from src.domain.netlist import Netlist
from src.domain.components.resistor import Resistor
from src.domain.components.vsource import VSource
from src.domain.components.diode import IdealDiode

# -------------------------------------------------
#  CONSTANTES UI
# -------------------------------------------------
GRID = 20
PIN_R = 9

DESC = {
    "R": "Resistor ideal. V = I·R.",
    "V": "Fuente de voltaje ideal (diferencia de potencial constante).",
    "D": "Diodo ideal: conduce del ánodo al cátodo (según polaridad).",
    "J": "Nodo de unión (•). Sirve como punto común de conexión.",
}

def snap(p):  # ajusta al grid
    return (round(p[0] / GRID) * GRID, round(p[1] / GRID) * GRID)


# -------------------------------------------------
#  UNIÓN–FIND (para conectividad)
# -------------------------------------------------
class UF:
    def __init__(self):
        self.p, self.r = {}, {}

    def find(self, x):
        if x not in self.p:
            self.p[x] = x
            self.r[x] = 0
        if self.p[x] != x:
            self.p[x] = self.find(self.p[x])
        return self.p[x]

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return
        if self.r[ra] < self.r[rb]:
            self.p[ra] = rb
        elif self.r[ra] > self.r[rb]:
            self.p[rb] = ra
        else:
            self.p[rb] = ra
            self.r[ra] += 1


# -------------------------------------------------
#  WIDGETS DE COMPONENTES
# -------------------------------------------------
class CompWidget(Widget):
    cid = StringProperty("")
    ctype = StringProperty("")  # R, V, D
    rot = NumericProperty(0)
    selected = BooleanProperty(False)
    props = DictProperty({})

    def __init__(self, **kw):
        super().__init__(**kw)
        self.size_hint = (None, None)
        self.size = (86, 36)
        self._drag = False
        self._last_tap = 0.0
        self.bind(pos=self._redraw, size=self._redraw,
                  rot=self._redraw, selected=self._redraw)
        Clock.schedule_once(lambda *_: self._redraw(), 0)

    def collide_point(self, x, y):
        cx, cy = self.center
        ang = math.radians(-(self.rot % 360))
        dx, dy = x - cx, y - cy
        c, s = math.cos(ang), math.sin(ang)
        lx, ly = dx * c - dy * s, dx * s + dy * c
        return (-48 <= lx <= 48) and (-14 <= ly <= 14)

    def pin_world(self) -> Dict[str, Tuple[float, float]]:
        out = {}
        cx, cy = self.center
        ang = math.radians(self.rot % 360)
        c, s = math.cos(ang), math.sin(ang)
        pins = {
            "R": {"A": (-44, 0), "B": (44, 0)},
            "V": {"+": (0, 22), "-": (0, -22)},
            "D": {"A": (-44, 0), "K": (44, 0)},
        }[self.ctype]
        for n, (lx, ly) in pins.items():
            x = lx * c - ly * s
            y = lx * s + ly * c
            out[n] = (cx + x, cy + y)
        return out

    def on_touch_down(self, touch):
        parent = self.parent
        if parent and getattr(parent, "mode", "") == "wire":
            return False
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)

        now = time.time()
        # doble clic → propiedades
        if now - self._last_tap < 0.35 and hasattr(parent, "open_properties"):
            parent.select_component(self)
            Clock.schedule_once(lambda dt: parent.open_properties(self), 0.05)
            self._last_tap = 0
            return True
        self._last_tap = now

        if hasattr(parent, "select_component"):
            parent.select_component(self)
        self._drag = True
        self._dx = touch.x - self.x
        self._dy = touch.y - self.y
        App.get_running_app().set_status(
            f"Seleccionado: {self.cid}. Doble clic para propiedades."
        )
        return True

    def on_touch_move(self, touch):
        if not self._drag:
            return super().on_touch_move(touch)
        nx = round((touch.x - self._dx) / GRID) * GRID
        ny = round((touch.y - self._dy) / GRID) * GRID
        self.pos = (nx, ny)
        if hasattr(self.parent, "redraw_wires"):
            self.parent.redraw_wires()
        return True

    def on_touch_up(self, touch):
        if not self._drag:
            return super().on_touch_up(touch)
        self._drag = False
        if hasattr(self.parent, "redraw_wires"):
            self.parent.redraw_wires()
        return True

    def _redraw(self, *_):
        self.canvas.clear()
        cx, cy = self.center
        with self.canvas:
            if self.selected:
                Color(1, 1, 1, 0.08)
                Rectangle(pos=(self.x - 4, self.y - 4),
                          size=(self.width + 8, self.height + 8))

            PushMatrix()
            Translate(cx, cy, 0)
            Rotate(angle=self.rot, axis=(0, 0, 1))

            # patitas
            Color(0.90, 0.94, 1, 1)
            if self.ctype in ("R", "D"):
                Line(points=[-60, 0, -44, 0], width=2)
                Line(points=[44, 0, 60, 0], width=2)
            else:
                Line(points=[0, 22, 0, 40], width=2)
                Line(points=[0, -22, 0, -40], width=2)

            # símbolo
            if self.ctype == "R":
                Color(1.0, 0.35, 0.35, 1)
                amp, seg, L = 8, 6, 88
                x0 = -L / 2
                pts = [x0, 0]
                for i in range(seg):
                    x1 = x0 + (L / seg) / 2
                    y1 = amp if i % 2 == 0 else -amp
                    x2 = x0 + (L / seg)
                    pts += [x1, y1, x2, 0]
                    x0 = x2
                Line(points=pts, width=2)
            elif self.ctype == "V":
                Color(0.96, 0.96, 0.99, 1)
                Ellipse(pos=(-16, -16), size=(32, 32))
                Color(0.12, 0.82, 0.72, 1)
                Line(points=[-5, 0, 5, 0], width=2)
                Line(points=[0, -5, 0, 5], width=2)
                Color(0.86, 0.25, 0.25, 1)
                Line(points=[-5, -10, 5, -10], width=2)
            else:
                Color(0.96, 0.96, 0.99, 1)
                Triangle(points=[-26, -10, -26, 10, 0, 0])
                Line(points=[2, -10, 2, 10], width=2)
            PopMatrix()

            # pines amarillos
            Color(0.93, 0.78, 0.18, 1)
            for _, (px, py) in self.pin_world().items():
                Ellipse(pos=(px - PIN_R / 2, py - PIN_R / 2),
                        size=(PIN_R, PIN_R))

            # etiqueta
            from kivy.core.text import Label as CoreLabel
            Color(0.86, 0.90, 1, 1)
            lab = CoreLabel(text=self.cid, font_size=14)
            lab.refresh()
            Rectangle(texture=lab.texture,
                      pos=(self.x + 4, self.top - 18),
                      size=lab.texture.size)


class Junction(Widget):
    jid = StringProperty("")
    selected = BooleanProperty(False)

    def __init__(self, **kw):
        super().__init__(**kw)
        self.size_hint = (None, None)
        self.size = (GRID, GRID)
        self.bind(pos=self._redraw, size=self._redraw, selected=self._redraw)
        Clock.schedule_once(lambda *_: self._redraw(), 0)

    def collide_point(self, x, y):
        return (abs(x - self.center_x) <= 8) and (abs(y - self.center_y) <= 8)

    def on_touch_down(self, touch):
        parent = self.parent
        if parent and getattr(parent, "mode", "") == "wire":
            return False
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)
        if hasattr(parent, "select_junction"):
            parent.select_junction(self)
        return True

    def world(self):
        return self.center

    def _redraw(self, *_):
        self.canvas.clear()
        with self.canvas:
            if self.selected:
                Color(1, 1, 1, 0.10)
                Rectangle(pos=(self.x - 6, self.y - 6),
                          size=(self.width + 12, self.height + 12))
            Color(0.93, 0.78, 0.18, 1)
            Ellipse(pos=(self.center_x - 4, self.center_y - 4), size=(8, 8))


@dataclass
class Wire:
    a: Tuple[str, str]
    b: Tuple[str, str]
    gfx: Optional[InstructionGroup] = None
    pts: Optional[List[float]] = None


# -------------------------------------------------
#  CANVAS PRINCIPAL
# -------------------------------------------------
class CircuitCanvas(FloatLayout):
    mode = StringProperty("select")
    selected: Optional[CompWidget] = None
    selected_j: Optional[Junction] = None

    def __init__(self, **kw):
        super().__init__(**kw)
        Clock.schedule_once(self._setup, 0.05)
        self.components: Dict[str, CompWidget] = {}
        self.junctions: Dict[str, Junction] = {}
        self._idc = {"R": 1, "V": 1, "D": 1, "J": 1}
        self.wires: List[Wire] = []
        self._wire_first: Optional[Tuple[str, str]] = None
        self._ghost: Optional[InstructionGroup] = None
        self._gnd: Optional[Tuple[str, str]] = None

    def _setup(self, *_):
        self.bind(size=self._grid, pos=self._grid)
        self._grid()

    def _grid(self, *_):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0.08, 0.10, 0.13, 1)
            Rectangle(pos=self.pos, size=self.size)
            Color(1, 1, 1, 0.055)
            x0, y0 = self.pos
            w, h = self.size
            for i in range(int(w // GRID) + 1):
                x = x0 + i * GRID
                Line(points=[x, y0, x, y0 + h], width=1)
            for j in range(int(h // GRID) + 1):
                y = y0 + j * GRID
                Line(points=[x0, y, x0 + w, y], width=1)

    # --------------- selección ---------------
    def select_component(self, cw):
        if self.selected and self.selected is not cw:
            self.selected.selected = False
        if self.selected_j:
            self.selected_j.selected = False
            self.selected_j = None
        self.selected = cw
        cw.selected = True
        App.get_running_app().update_inspector(cw)

    def select_junction(self, j):
        if self.selected:
            self.selected.selected = False
            self.selected = None
        if self.selected_j and self.selected_j is not j:
            self.selected_j.selected = False
        self.selected_j = j
        j.selected = True
        app = App.get_running_app()
        app.root.ids.ins_name.text = j.jid
        app.root.ids.ins_value.text = "-"
        app.root.ids.ins_desc.text = DESC["J"]

    def set_mode(self, m):
        self.mode = m
        self._wire_first = None
        self._clear_ghost()
        names = {
            "select": "Seleccionar",
            "add_R": "Agregar Resistor",
            "add_V": "Agregar Fuente",
            "add_D": "Agregar Diodo",
            "add_J": "Agregar Nodo",
            "wire": "Conectar con Cable",
            "set_gnd": "Establecer Tierra (GND)",
        }
        App.get_running_app().set_status(f"Modo: {names.get(m, m)}")

    # --------------- altas/bajas ---------------
    def add_component(self, t):
        cid = f"{t}{self._idc[t]}"
        self._idc[t] += 1
        props = {
            "R": {"R": 1000.0},
            "V": {"V": 5.0},
            "D": {"polarity": "A_to_K"},
        }.get(t, {})
        cw = CompWidget(cid=cid, ctype=t, props=props)
        cw.center = snap((self.center_x, self.center_y))
        self.add_widget(cw)
        self.components[cid] = cw
        self.select_component(cw)

    def add_junction(self):
        jid = f"J{self._idc['J']}"
        self._idc["J"] += 1
        j = Junction(jid=jid)
        j.center = snap((self.center_x, self.center_y))
        self.add_widget(j)
        self.junctions[jid] = j
        self.select_junction(j)

    def rotate_selected(self):
        if not self.selected:
            return
        self.selected.rot = (self.selected.rot + 90) % 360
        self.redraw_wires()
        App.get_running_app().update_inspector(self.selected)

    def delete_selected(self):
        if self.selected:
            cid = self.selected.cid
            to_keep = []
            for w in self.wires:
                if w.a[0] == cid or w.b[0] == cid:
                    if w.gfx:
                        self.canvas.after.remove(w.gfx)
                else:
                    to_keep.append(w)
            self.wires = to_keep
            self.remove_widget(self.selected)
            self.components.pop(cid, None)
            self.selected = None
        elif self.selected_j:
            jid = self.selected_j.jid
            to_keep = []
            for w in self.wires:
                if w.a[0] == f"J:{jid}" or w.b[0] == f"J:{jid}":
                    if w.gfx:
                        self.canvas.after.remove(w.gfx)
                else:
                    to_keep.append(w)
            self.wires = to_keep
            self.remove_widget(self.selected_j)
            self.junctions.pop(jid, None)
            self.selected_j = None
        App.get_running_app().set_status("Elemento y cables asociados eliminados.")
        self._clear_ghost()

    # --------------- utilería ---------------
    def _hit_pin(self, x, y) -> Optional[Tuple[str, str]]:
        for cid, cw in self.components.items():
            for pname, (px, py) in cw.pin_world().items():
                if (x - px) ** 2 + (y - py) ** 2 <= (PIN_R * 1.3) ** 2:
                    return (cid, pname)
        for jid, j in self.junctions.items():
            px, py = j.world()
            if (x - px) ** 2 + (y - py) ** 2 <= (GRID * 0.6) ** 2:
                return (f"J:{jid}", "J")
        return None

    def _get_obstacles(self) -> set:
        occ = set()
        # cuerpos
        for cw in self.components.values():
            cx, cy = cw.center
            hw = (cw.width / 2 // GRID + 1) * GRID
            hh = (cw.height / 2 // GRID + 1) * GRID
            min_x, max_x = snap((cx - hw, 0))[0], snap((cx + hw, 0))[0]
            min_y, max_y = snap((0, cy - hh))[1], snap((0, cy + hh))[1]
            for x in range(min_x, max_x + GRID, GRID):
                for y in range(min_y, max_y + GRID, GRID):
                    occ.add((x, y))

        # cables ya trazados
        for w in self.wires:
            if not w.pts:
                continue
            for i in range(0, len(w.pts) - 2, 2):
                x1, y1 = snap((w.pts[i], w.pts[i + 1]))
                x2, y2 = snap((w.pts[i + 2], w.pts[i + 3]))
                if x1 == x2:
                    for y in range(min(y1, y2), max(y1, y2) + GRID, GRID):
                        occ.add((x1, y))
                else:
                    for x in range(min(x1, x2), max(x1, x2) + GRID, GRID):
                        occ.add((x, y1))

        def clear_neighborhood(x, y):
            for dx, dy in [(0, 0), (GRID, 0), (-GRID, 0), (0, GRID), (0, -GRID)]:
                occ.discard((x + dx, y + dy))

        # “puertas” alrededor de pines/nodos
        for cw in self.components.values():
            for _, (px, py) in cw.pin_world().items():
                xx, yy = snap((px, py))
                clear_neighborhood(xx, yy)
        for j in self.junctions.values():
            xx, yy = snap(j.world())
            clear_neighborhood(xx, yy)

        return occ

    def _find_path_astar(self, p1, p2) -> Optional[List[float]]:
        start, goal = snap(p1), snap(p2)
        occ = self._get_obstacles()
        occ.discard(start)
        occ.discard(goal)

        def h(a, b): return abs(a[0] - b[0]) + abs(a[1] - b[1])

        open_set = []
        heapq.heappush(open_set, (h(start, goal), 0, start, [start]))
        visited = {start}
        while open_set:
            f, g, pos, path = heapq.heappop(open_set)
            if pos == goal:
                return [c for pt in path for c in pt]
            for dx, dy in [(0, GRID), (0, -GRID), (GRID, 0), (-GRID, 0)]:
                nb = (pos[0] + dx, pos[1] + dy)
                if not (self.x <= nb[0] <= self.right and self.y <= nb[1] <= self.top):
                    continue
                if nb in occ or nb in visited:
                    continue
                visited.add(nb)
                g2 = g + GRID
                f2 = g2 + h(nb, goal)
                heapq.heappush(open_set, (f2, g2, nb, path + [nb]))
        return None

    def _clear_ghost(self):
        if self._ghost:
            self.canvas.after.remove(self._ghost)
            self._ghost = None

    def _pin_world(self, comp_id, pin):
        if comp_id.startswith("J:"):
            return self.junctions[comp_id.split(":")[1]].world()
        return self.components[comp_id].pin_world()[pin]

    def _update_ghost(self, cursor_pos):
        if not self._wire_first or cursor_pos is None:
            self._clear_ghost()
            return
        p1 = self._pin_world(*self._wire_first)
        hit = self._hit_pin(*cursor_pos)
        self._clear_ghost()
        self._ghost = InstructionGroup()
        if not hit:
            self._ghost.add(Color(1.0, 0.3, 0.3, 0.6))
            self._ghost.add(
                Line(points=[p1[0], p1[1], cursor_pos[0], cursor_pos[1]],
                     width=2, dash_length=4)
            )
            self.canvas.after.add(self._ghost)
            return
        p2 = self._pin_world(*hit)
        pts = self._find_path_astar(p1, p2)
        if pts:
            self._ghost.add(Color(0.25, 0.7, 1.0, 0.8))
            self._ghost.add(Line(points=pts, width=3, cap="round"))
        else:
            self._ghost.add(Color(1.0, 0.2, 0.2, 0.7))
            self._ghost.add(
                Line(points=[p1[0], p1[1], p2[0], p2[1]], width=2, dash_length=4)
            )
        self.canvas.after.add(self._ghost)

    # --------------- interacción ---------------
    def on_touch_down(self, touch):
        if super().on_touch_down(touch):
            return True
        if not self.collide_point(*touch.pos):
            return False

        if self.mode in ("add_R", "add_V", "add_D"):
            self.add_component(self.mode.split("_")[1])
            App.get_running_app().set_status(
                "Componente agregado. Arrastra para mover."
            )
            return True

        if self.mode == "add_J":
            self.add_junction()
            App.get_running_app().set_status("Nodo agregado. Conéctalo con cables.")
            return True

        if self.mode == "wire":
            hit = self._hit_pin(*touch.pos)
            if not hit:
                App.get_running_app().set_status(
                    "❌ Click solo en pines (círculos dorados) o nodos (•)"
                )
                return True
            if not self._wire_first:
                self._wire_first = hit
                App.get_running_app().set_status(
                    f"Primer pin: {hit[0]}:{hit[1]}. Ahora el segundo pin."
                )
                return True
            a = self._wire_first
            b = hit
            if a != b:
                self._add_wire(a, b)
                App.get_running_app().set_status(
                    f"Cable: {a[0]}:{a[1]} → {b[0]}:{b[1]}"
                )
            else:
                App.get_running_app().set_status(
                    "❌ No puedes conectar un pin consigo mismo."
                )
            self._wire_first = None
            self._clear_ghost()
            return True

        if self.mode == "set_gnd":
            hit = self._hit_pin(*touch.pos)
            if not hit:
                App.get_running_app().set_status("Selecciona un pin o nodo para GND.")
                return True
            self._gnd = hit
            App.get_running_app().set_status(f"✅ GND fijada en {hit[0]}:{hit[1]}")
            return True

        return False

    def on_touch_move(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_move(touch)
        if self.mode == "wire" and self._wire_first:
            self._update_ghost(touch.pos)
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_up(touch)
        return super().on_touch_up(touch)

    # --------------- cables ---------------
    def _add_wire(self, a, b):
        p1 = self._pin_world(*a)
        p2 = self._pin_world(*b)
        pts = self._find_path_astar(p1, p2)
        if not pts:
            App.get_running_app().set_status(
                "No hay ruta limpia entre esos puntos."
            )
            return
        w = Wire(a, b, pts=pts)
        self._draw_wire(w)
        self.wires.append(w)

    def _draw_wire(self, w):
        if w.gfx:
            self.canvas.after.remove(w.gfx)
        if not w.pts:
            return
        grp = InstructionGroup()
        grp.add(Color(0.02, 0.03, 0.05, 1))
        grp.add(Line(points=w.pts, width=4, cap="round"))
        grp.add(Color(0.35, 0.80, 1.0, 1))
        grp.add(Line(points=w.pts, width=2.2, cap="round"))
        self.canvas.after.add(grp)
        w.gfx = grp

    def redraw_wires(self):
        for w in self.wires:
            w.pts = (
                self._find_path_astar(self._pin_world(*w.a),
                                      self._pin_world(*w.b)) or w.pts
            )
            self._draw_wire(w)

    # --------------- conectividad ---------------
    def _connectivity_ok(self) -> Tuple[bool, str]:
        uf = UF()
        # cables
        for w in self.wires:
            uf.union(f"{w.a[0]}:{w.a[1]}", f"{w.b[0]}:{w.b[1]}")

        pins: List[Tuple[str, str]] = []
        for cid, cw in self.components.items():
            for pname in cw.pin_world().keys():
                pins.append((cid, pname))
        for jid in self.junctions.keys():
            pins.append((f"J:{jid}", "J"))
        if not pins:
            return False, "Añade al menos un componente."

        groups: Dict[str, List[Tuple[str, str]]] = {}
        for cid, pn in pins:
            r = uf.find(f"{cid}:{pn}")
            groups.setdefault(r, []).append((cid, pn))

        names: Dict[str, str] = {}
        k = 1
        if self._gnd:
            names[uf.find(f"{self._gnd[0]}:{self._gnd[1]}")] = "GND"
        for r in groups.keys():
            if r not in names:
                names[r] = f"N{k}"
                k += 1

        # grafo de nodos
        adj: Dict[str, set] = {names[r]: set() for r in groups.keys()}
        used_nodes: set = set()

        for cid, cw in self.components.items():
            pin2node: Dict[str, str] = {}
            for pname in cw.pin_world().keys():
                root = uf.find(f"{cid}:{pname}")
                pin2node[pname] = names[root]
                used_nodes.add(names[root])

            if cw.ctype == "R":
                n1, n2 = pin2node["A"], pin2node["B"]
            elif cw.ctype == "V":
                n1, n2 = pin2node["+"], pin2node["-"]
            else:
                n1, n2 = pin2node["A"], pin2node["K"]

            adj.setdefault(n1, set()).add(n2)
            adj.setdefault(n2, set()).add(n1)

        if not used_nodes:
            return False, "Coloca y conecta componentes antes de simular."

        if self._gnd:
            ref_node = names[uf.find(f"{self._gnd[0]}:{self._gnd[1]}")]
        else:
            ref_node = next(iter(used_nodes))

        visited = set()
        stack = [ref_node]
        while stack:
            u = stack.pop()
            if u in visited:
                continue
            visited.add(u)
            for v in adj.get(u, ()):
                if v not in visited:
                    stack.append(v)

        not_reached = used_nodes - visited
        if not_reached:
            listado = ", ".join(sorted(not_reached))
            return False, (
                "Hay subconjuntos aislados (nodos no alcanzados desde la referencia): "
                f"{listado}. Conecta las ramas o fija GND en un nodo del lazo principal."
            )
        return True, "Conectividad OK."

    # --------------- netlist ---------------
    def build_netlist(self) -> Netlist:
        uf = UF()
        for w in self.wires:
            uf.union(f"{w.a[0]}:{w.a[1]}", f"{w.b[0]}:{w.b[1]}")

        pins = []
        for cid, cw in self.components.items():
            for pname in cw.pin_world().keys():
                pins.append((cid, pname))
        for jid in self.junctions.keys():
            pins.append((f"J:{jid}", "J"))

        groups = {}
        for cid, pn in pins:
            r = uf.find(f"{cid}:{pn}")
            groups.setdefault(r, []).append((cid, pn))

        names = {}
        k = 1
        if self._gnd:
            names[uf.find(f"{self._gnd[0]}:{self._gnd[1]}")] = "GND"
        if "GND" not in names.values() and groups:
            first_key = next(iter(groups.keys()))
            names[first_key] = "GND"
        for r in groups.keys():
            if r not in names:
                names[r] = f"N{k}"
                k += 1

        nl = Netlist()
        for r in groups.keys():
            nl.add_node(names[r], is_ground=(names[r] == "GND"))

        for cid, cw in self.components.items():
            mp = {pn: names[uf.find(f"{cid}:{pn}")] for pn in cw.pin_world().keys()}
            if cw.ctype == "R":
                nl.add_component(
                    Resistor(
                        id=cid, n1=mp["A"], n2=mp["B"],
                        R=float(cw.props.get("R", 1000.0))
                    )
                )
            elif cw.ctype == "V":
                nl.add_component(
                    VSource(
                        id=cid, n1=mp["+"], n2=mp["-"],
                        V=float(cw.props.get("V", 5.0))
                    )
                )
            else:
                nl.add_component(
                    IdealDiode(
                        id=cid, n1=mp["A"], n2=mp["K"],
                        polarity=cw.props.get("polarity", "A_to_K"),
                    )
                )
        return nl

    # --------------- acciones ---------------
    def simulate_from_canvas(self):
        try:
            ok, msg = self._connectivity_ok()
            app = App.get_running_app()
            if not ok:
                app.root.ids.lbl_info.text = msg
                app.set_status(msg)
                return
            nl = self.build_netlist()
            sol = simulate(nl)
            app.show_results(sol)
            app.set_status("Simulación lista.")
        except Exception as e:
            app = App.get_running_app()
            app.set_status(f"Error: {e}")
            app.info_popup("Error de simulación", str(e))

    def export_pdf_from_canvas(self):
        """
        1) valida conectividad
        2) simula
        3) screenshot canvas → base64
        4) diálogo 'Guardar como' para el PDF
        """
        try:
            ok, msg = self._connectivity_ok()
            app = App.get_running_app()
            if not ok:
                app.root.ids.lbl_info.text = msg
                app.set_status(msg)
                return

            nl = self.build_netlist()
            sol = simulate(nl)

            solution = {
                "node_voltages": dict(getattr(sol, "node_voltages", {})),
                "branch_currents": dict(getattr(sol, "branch_currents", {})),
                "kcl": dict(getattr(sol, "kcl", {})) if hasattr(sol, "kcl") else {},
                "kvl": dict(getattr(sol, "kvl", {})) if hasattr(sol, "kvl") else {},
                "netlist": nl.to_dict() if hasattr(nl, "to_dict") else {},
            }

            tmp_path = os.path.join(tempfile.gettempdir(), "cirkit_canvas.png")
            self.export_to_png(tmp_path)
            with open(tmp_path, "rb") as f:
                png_b64 = base64.b64encode(f.read()).decode("ascii")
            try:
                os.remove(tmp_path)
            except OSError:
                pass

            root = tk.Tk(); root.withdraw()
            fname = filedialog.asksaveasfilename(
                title="Guardar reporte PDF",
                defaultextension=".pdf",
                filetypes=[("Archivo PDF", "*.pdf")],
                initialfile="reporte_cirkit.pdf",
            )
            root.destroy()
            if not fname:
                App.get_running_app().set_status("Exportación cancelada.")
                return

            export_solution_pdf(fname, solution, diagram=self.to_json(), png_b64=png_b64)
            app.info_popup("PDF", f"PDF exportado en:\n{fname}")
            app.set_status("PDF exportado.")
        except Exception as e:
            app = App.get_running_app()
            app.set_status(f"Error: {e}")
            app.info_popup("Error de exportación", str(e))

    # --------------- serialización ---------------
    def to_json(self) -> Dict[str, Any]:
        return {
            "components": [
                {
                    "id": cw.cid, "type": cw.ctype,
                    "x": cw.center_x, "y": cw.center_y,
                    "rot": cw.rot, "props": dict(cw.props),
                }
                for cw in self.components.values()
            ],
            "junctions": [
                {"id": jid, "x": j.center_x, "y": j.center_y}
                for jid, j in self.junctions.items()
            ],
            "wires": [{"a": w.a, "b": w.b} for w in self.wires],
            "gnd": self._gnd,
        }

    def from_json(self, data: Dict[str, Any]):
        # limpiar
        for w in self.wires:
            if w.gfx:
                self.canvas.after.remove(w.gfx)
        for cw in list(self.components.values()):
            self.remove_widget(cw)
        for j in list(self.junctions.values()):
            self.remove_widget(j)
        self.wires.clear()
        self.components.clear()
        self.junctions.clear()
        self.selected = None
        self.selected_j = None
        self._gnd = None
        self._idc = {"R": 1, "V": 1, "D": 1, "J": 1}

        # componentes
        for c in data.get("components", []):
            cw = CompWidget(
                cid=c["id"], ctype=c["type"],
                rot=int(c.get("rot", 0)),
                props=c.get("props", {}),
            )
            cw.center = (c["x"], c["y"])
            self.add_widget(cw)
            self.components[cw.cid] = cw
            t = cw.ctype
            try:
                n = int("".join(filter(str.isdigit, cw.cid)))
            except Exception:
                n = 0
            self._idc[t] = max(self._idc[t], n + 1)

        # nodos
        for j in data.get("junctions", []):
            jj = Junction(jid=j["id"])
            jj.center = (j["x"], j.get("y", 0))
            self.add_widget(jj)
            self.junctions[jj.jid] = jj
            try:
                n = int("".join(filter(str.isdigit, jj.jid)))
            except Exception:
                n = 0
            self._idc["J"] = max(self._idc["J"], n + 1)

        # cables
        for w in data.get("wires", []):
            self._add_wire(tuple(w["a"]), tuple(w["b"]))

        # gnd
        gnd_data = data.get("gnd")
        self._gnd = tuple(gnd_data) if isinstance(gnd_data, list) else gnd_data

        self.redraw_wires()
        App.get_running_app().set_status("Diagrama cargado.")

    # --------------- propiedades ---------------
    def open_properties(self, cw: "CompWidget"):
        box = BoxLayout(orientation="vertical", spacing=8, padding=10)
        title_map = {"R": "Resistor", "V": "Fuente de Voltaje", "D": "Diodo"}
        title = title_map.get(cw.ctype, "Componente")

        if cw.ctype == "R":
            ti = TextInput(
                text=str(cw.props.get("R", 1000.0)),
                multiline=False, input_filter="float",
            )
            box.add_widget(Label(text="Resistencia (Ω):"))
            box.add_widget(ti)
            target = ti
        elif cw.ctype == "V":
            ti = TextInput(
                text=str(cw.props.get("V", 5.0)),
                multiline=False, input_filter="float",
            )
            box.add_widget(Label(text="Voltaje (V):"))
            box.add_widget(ti)
            target = ti
        else:
            sp = Spinner(
                text=cw.props.get("polarity", "A_to_K"),
                values=["A_to_K", "K_to_A"],
            )
            box.add_widget(Label(text="Polaridad:"))
            box.add_widget(sp)
            target = sp

        btns = BoxLayout(size_hint_y=None, height="42dp", spacing=8)

        def _ok(*_):
            try:
                if cw.ctype == "R":
                    cw.props["R"] = float(target.text)
                elif cw.ctype == "V":
                    cw.props["V"] = float(target.text)
                else:
                    cw.props["polarity"] = target.text
                p.dismiss()
                App.get_running_app().update_inspector(cw)
                cw._redraw()
            except Exception as e:
                App.get_running_app().set_status(f"Error: {e}")

        b1 = Button(text="Aceptar"); b1.bind(on_release=_ok)
        b2 = Button(text="Cancelar"); b2.bind(on_release=lambda *_: p.dismiss())
        btns.add_widget(b1); btns.add_widget(b2)
        box.add_widget(btns)
        p = Popup(
            title=f"Propiedades: {title} {cw.cid}",
            content=box, size_hint=(0.5, 0.4),
        )
        p.open()


# -------------------------------------------------
#  APP
# -------------------------------------------------
class Contenedor_01(BoxLayout):
    pass


def _base_assets_dir() -> pathlib.Path:
    """Devuelve carpeta base de recursos tanto en dev como en build (.exe)."""
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return pathlib.Path(meipass)
    return pathlib.Path(__file__).resolve().parents[2]  # .../src/ui


def _icons_dir() -> pathlib.Path:
    base = _base_assets_dir()
    candidates = [
        base / "kivy" / "icons",
        base / "icons",
        ROOT / "src" / "ui" / "kivy" / "icons",
    ]
    for p in candidates:
        if p.exists():
            return p
    return candidates[-1]


class CirKitApp(App):
    title = "CirKit - Simulador de Circuitos Eléctricos"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.kv_file = ""

        # recursos (solo app icon)
        icons = _icons_dir()
        resource_add_path(str(icons))
        try:
            ico = icons / "app_icon.ico"
            png = icons / "app_icon.png"
            if ico.exists():
                Window.set_icon(str(ico))
            elif png.exists():
                Window.set_icon(str(png))
        except Exception:
            pass

        # tamaño/estado de ventana
        try:
            Window.minimum_width  = 1100
            Window.minimum_height = 650
            if Window.width < 1100 or Window.height < 650:
                Window.size = (1280, 780)
            Window.maximize()
        except Exception:
            pass

    def build(self):
        kv_path = str(pathlib.Path(__file__).with_suffix(".kv"))
        return Builder.load_file(kv_path)

    # -------- helpers seguros --------
    def _get_root_widget(self):
        return self.root

    def _get_ids(self) -> Dict[str, Any]:
        r = self._get_root_widget()
        return getattr(r, "ids", {})

    # ----------------------------------
    def set_status(self, txt: str) -> None:
        ids = self._get_ids()
        lbl = ids.get("status_label")
        if lbl is not None:
            lbl.text = txt

    def update_inspector(self, cw: 'CompWidget') -> None:
        ids = self._get_ids()
        ins_name = ids.get("ins_name")
        ins_value = ids.get("ins_value")
        ins_desc = ids.get("ins_desc")

        if ins_name is None or ins_value is None or ins_desc is None:
            return

        ins_name.text = cw.cid
        if cw.ctype == "R":
            val = f"{cw.props.get('R', 1000.0)} Ω"
        elif cw.ctype == "V":
            val = f"{cw.props.get('V', 5.0)} V"
        else:
            val = cw.props.get("polarity", "A_to_K")
        ins_value.text = val
        ins_desc.text = DESC.get(cw.ctype, "")

    def show_results(self, sol) -> None:
        ids = self._get_ids()
        lbl = ids.get("lbl_info")
        if lbl is None:
            return
        lines = ["[b]=== RESULTADOS ===[/b]", "[b]Voltajes nodales:[/b]"]
        for k, v in sol.node_voltages.items():
            lines.append(f"• {k}: {v:.6f} V")
        lines += ["", "[b]Corrientes:[/b]"]
        for k, i in sol.branch_currents.items():
            lines.append(f"• {k}: {i:.9f} A")
        lbl.markup = True
        lbl.text = "\n".join(lines)

    def info_popup(self, title: str, msg: str) -> None:
        content = Label(text=str(msg), halign="left", valign="middle")
        pop = Popup(title=title, content=content, size_hint=(0.6, 0.5))
        content.bind(
            size=lambda *_: setattr(content, "text_size", (content.width - 20, None))
        )
        pop.open()

    # ---------------- Guardar / Abrir ----------------
    def prompt_save(self) -> None:
        ids = self._get_ids()
        canvas = ids.get("canvas_area")
        if canvas is None:
            self.info_popup("Error", "No se encontró el canvas para guardar.")
            return
        try:
            root = tk.Tk(); root.withdraw()
            fname = filedialog.asksaveasfilename(
                title="Guardar diagrama (.json)",
                defaultextension=".json",
                filetypes=[("Diagramas CirKit", "*.json")],
                initialfile="diagrama.json",
            )
            root.destroy()
            if not fname:
                self.set_status("Guardado cancelado.")
                return
            data = canvas.to_json()
            with open(fname, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            self.info_popup("Guardar", f"Diagrama guardado en:\n{fname}")
        except Exception as e:
            self.info_popup("Error al Guardar", str(e))

    def prompt_open(self) -> None:
        ids = self._get_ids()
        canvas = ids.get("canvas_area")
        if canvas is None:
            self.info_popup("Error", "No se encontró el canvas para abrir.")
            return
        try:
            root = tk.Tk(); root.withdraw()
            fname = filedialog.askopenfilename(
                title="Abrir diagrama (.json)",
                filetypes=[("Diagramas CirKit", "*.json"), ("Todos los archivos", "*.*")],
            )
            root.destroy()
            if not fname:
                return
            with open(fname, "r", encoding="utf-8") as f:
                data = json.load(f)
            canvas.from_json(data)
            self.info_popup("Abrir", f"Configuración cargada:\n{fname}")
        except Exception as e:
            self.info_popup("Error al Abrir", str(e))

    # ---------------- Tutorial + Plantillas ----------------
    def open_tutorial_popup(self, *_):
        ids = self._get_ids()
        if not ids:
            return

        box = BoxLayout(orientation="vertical", spacing=10, padding=14)
        tips = (
            "1) En la barra elige R, V, D o Nodo.\n"
            "2) Colócalos en el canvas (ajuste al grid).\n"
            "3) Usa 'Cable' para conectar pines/nodos.\n"
            "4) Usa 'Tierra (GND)' en el nodo de referencia.\n"
            "5) Doble clic sobre un componente para editar su valor.\n"
            "6) 'Simular' muestra voltajes y corrientes.\n"
            "7) 'Exportar PDF' guarda un reporte con captura del esquema."
        )
        lbl = Label(text=tips, halign="left", valign="top")
        lbl.bind(size=lambda *_: setattr(lbl, "text_size", (lbl.width, None)))
        box.add_widget(lbl)

        def _tpl_btn(txt, loader):
            b = Button(text=txt, size_hint_y=None, height="42dp")
            b.bind(on_release=lambda *_: loader())
            return b

        btns = BoxLayout(size_hint_y=None, height="48dp", spacing=8)
        btns.add_widget(_tpl_btn("Plantilla 1: V–R–GND",
                      lambda: self.load_template("plantilla_1")))
        btns.add_widget(_tpl_btn("Plantilla 2: V–D–GND",
                      lambda: self.load_template("plantilla_2")))
        btns.add_widget(_tpl_btn("Plantilla 3: Serie R1–R2 con V",
                      lambda: self.load_template("plantilla_3")))
        btns.add_widget(_tpl_btn("Plantilla 4: Nodo común (R y D)",
                      lambda: self.load_template("plantilla_4")))
        box.add_widget(btns)

        close_bar = BoxLayout(size_hint_y=None, height="48dp", spacing=8)
        p = Popup(title="Tutorial rápido de CirKit", content=box, size_hint=(0.8, 0.8))
        bclose = Button(text="Cerrar"); bclose.bind(on_release=lambda *_: p.dismiss())
        close_bar.add_widget(bclose)
        box.add_widget(close_bar)
        p.open()

    def load_template(self, name: str):
        ids = self._get_ids()
        canvas: CircuitCanvas = ids.get("canvas_area")  # type: ignore
        if not canvas:
            return

        # helpers
        def place(cw, x, y, rot=0):
            cw.center = (x, y); cw.rot = rot; canvas.add_widget(cw)
        def wire(a, ap, b, bp):
            canvas._add_wire(
                (a.cid if hasattr(a, "cid") else f"J:{a.jid}", ap),
                (b.cid if hasattr(b, "cid") else f"J:{b.jid}", bp)
            )

        # limpiar
        canvas.from_json({"components": [], "junctions": [], "wires": [], "gnd": None})

        cx, cy = canvas.center_x, canvas.center_y
        if name == "plantilla_1":  # V–R–GND
            v = CompWidget(cid="V1", ctype="V", props={"V": 5.0}); place(v, cx-200, cy,   90)
            r = CompWidget(cid="R1", ctype="R", props={"R": 1000}); place(r, cx-60,  cy,   0)
            g = Junction(jid="J1"); place(g, cx+100, cy, 0)
            wire(v, "+", r, "A"); wire(r, "B", g, "J"); wire(v, "-", g, "J")
            canvas._gnd = (f"J:{g.jid}", "J")
        elif name == "plantilla_2":  # V–D–GND
            v = CompWidget(cid="V1", ctype="V", props={"V": 5.0}); place(v, cx-200, cy, 90)
            d = CompWidget(cid="D1", ctype="D", props={"polarity": "A_to_K"}); place(d, cx-60, cy, 0)
            g = Junction(jid="J1"); place(g, cx+100, cy, 0)
            wire(v, "+", d, "A"); wire(d, "K", g, "J"); wire(v, "-", g, "J")
            canvas._gnd = (f"J:{g.jid}", "J")
        elif name == "plantilla_3":  # V con R1–R2 en serie
            v = CompWidget(cid="V1", ctype="V", props={"V": 12.0}); place(v, cx-240, cy, 90)
            r1 = CompWidget(cid="R1", ctype="R", props={"R": 1000}); place(r1, cx-100, cy, 0)
            r2 = CompWidget(cid="R2", ctype="R", props={"R": 2000}); place(r2, cx+40,  cy, 0)
            g = Junction(jid="J1"); place(g, cx+180, cy, 0)
            wire(v, "+", r1, "A"); wire(r1, "B", r2, "A"); wire(r2, "B", g, "J"); wire(v, "-", g, "J")
            canvas._gnd = (f"J:{g.jid}", "J")
        else:  # plantilla_4: nodo común (R y D en paralelo)
            v = CompWidget(cid="V1", ctype="V", props={"V": 9.0}); place(v, cx-260, cy, 90)
            jtop = Junction(jid="J1"); jbot = Junction(jid="J2")
            place(jtop, cx-60, cy+30, 0); place(jbot, cx-60, cy-30, 0)
            r = CompWidget(cid="R1", ctype="R", props={"R": 470}); place(r, cx+60, cy+30, 0)
            d = CompWidget(cid="D1", ctype="D", props={"polarity": "A_to_K"}); place(d, cx+60, cy-30, 0)
            g = Junction(jid="J3"); place(g, cx+200, cy, 0)
            wire(v, "+", jtop, "J"); wire(jtop, "J", r, "A"); wire(r, "B", g, "J")
            wire(v, "-", jbot, "J"); wire(jbot, "J", d, "A"); wire(d, "K", g, "J")
            canvas._gnd = (f"J:{g.jid}", "J")

        canvas.redraw_wires()
        self.set_status(f"Plantilla cargada: {name}")


# -------------------------------------------------
#  MAIN
# -------------------------------------------------
if __name__ == "__main__":
    CirKitApp().run()
