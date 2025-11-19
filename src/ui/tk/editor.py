import tkinter as tk
from tkinter import simpledialog, messagebox

from src.domain.netlist import Netlist
from src.domain.components.resistor import Resistor
from src.domain.components.vsource import VSource
from src.domain.components.diode import IdealDiode


GRID = 20

class Editor(tk.Frame):
    def __init__(self, parent, netlist: Netlist):
        super().__init__(parent)
        self.netlist = netlist
        self.canvas = tk.Canvas(self, bg="#0e1217")
        self.canvas.pack(fill="both", expand=True)
        self._init_bindings()
        self.mode = None  # "place_R", "place_V", "place_D", "wire"
        self.temp = {}
        self.nodes = {}  # xy-> node_id
        self.items = {}  # item_id -> comp_id

    def _init_bindings(self):
        self.canvas.bind("<Button-1>", self.on_click)
        self.canvas.bind("<Motion>", self._show_coords)

    def set_mode(self, mode: str):
        self.mode = mode

    def on_click(self, e):
        x, y = self._snap(e.x), self._snap(e.y)
        if self.mode in ("place_R","place_V","place_D"):
            cid = simpledialog.askstring("ID del componente", "Ej: R1 / V1 / D1", parent=self)
            if not cid: return
            n1 = simpledialog.askstring("Nodo n1", "Ej: N1", parent=self) or "N1"
            n2 = simpledialog.askstring("Nodo n2", "Ej: GND", parent=self) or "GND"
            if self.mode == "place_R":
                R = float(simpledialog.askstring("R (ohmios)", "Ej: 1000", parent=self) or "1000")
                c = Resistor(id=cid, n1=n1, n2=n2, R=R, x=x, y=y)
            elif self.mode == "place_V":
                V = float(simpledialog.askstring("V (voltios)", "Ej: 5", parent=self) or "5")
                c = VSource(id=cid, n1=n1, n2=n2, V=V, x=x, y=y)
            else:
                c = IdealDiode(id=cid, n1=n1, n2=n2, polarity="A_to_K", x=x, y=y)
            self.netlist.add_component(c)
            self._draw_component(c)
        elif self.mode == "wire":
            # primer clic: origen; segundo clic: destino (crea línea)
            if "p1" not in self.temp:
                self.temp["p1"] = (x,y)
            else:
                x1,y1 = self.temp.pop("p1")
                self.canvas.create_line(x1,y1,x,y,fill="#66d9ef",width=2)
        else:
            # toggle GND en nodo por conveniencia
            pass

    def load_from_netlist(self):
        self.canvas.delete("all")
        for c in self.netlist.components:
            if getattr(c, "x", None) is None or getattr(c, "y", None) is None:
                continue
            self._draw_component(c)

    def _draw_component(self, c):
        x, y = int(c.x), int(c.y)
        w, h = 60, 30
        color = {"R":"#f1fa8c", "V":"#50fa7b", "D":"#ff79c6"}.get(c.kind,"#bd93f9")
        rect = self.canvas.create_rectangle(x-w//2,y-h//2,x+w//2,y+h//2, outline=color, width=2)
        label = self.canvas.create_text(x, y, text=f"{c.id}\n{c.kind}", fill="white")
        self.items[rect] = c.id
        self.items[label] = c.id

    def _snap(self, v): return (v // GRID) * GRID

    def _show_coords(self, e):
        self.master.title(f"Sim-Elec — ({self._snap(e.x)}, {self._snap(e.y)})")
