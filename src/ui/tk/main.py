import tkinter as tk
from tkinter import filedialog, messagebox
import os
from src.app.serialization import load_json
from src.app.simulate import simulate
from src.app.export_pdf import export_solution_pdf
from src.ui.tk.tutorials import open_tutorial
from src.ui.tk.errors import guard

TEMPLATES = {
    "Divisor R (VR)": "examples/vr_divisor.json",
    "Diodo ON": "examples/diode_on.json",
    "Diodo OFF": "examples/diode_off.json"
}

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Sim-Elec")
        self.geometry("820x560")
        self.netlist_path = None
        self.text = tk.Text(self, wrap="word")
        self.text.pack(fill="both", expand=True)
        self._menu()
        self.after(300, lambda: open_tutorial(self, "bienvenida"))

    def _menu(self):
        m = tk.Menu(self)
        filem = tk.Menu(m, tearoff=0)
        filem.add_command(label="Abrir netlist...", command=self.open_netlist)
        filem.add_command(label="Exportar PDF...", command=self.export_pdf)
        filem.add_separator()
        filem.add_command(label="Salir", command=self.destroy)
        m.add_cascade(label="Archivo", menu=filem)

        templ = tk.Menu(m, tearoff=0)
        for label, relpath in TEMPLATES.items():
            templ.add_command(label=label, command=lambda p=relpath: self.load_template(p))
        m.add_cascade(label="Plantillas", menu=templ)

        runm = tk.Menu(m, tearoff=0)
        runm.add_command(label="Simular", command=self.run_sim)
        m.add_cascade(label="Simulación", menu=runm)

        viewm = tk.Menu(m, tearoff=0)
        viewm.add_command(label="Abrir Editor", command=self.open_editor)
        m.add_cascade(label="Editor", menu=viewm)

        helpm = tk.Menu(m, tearoff=0)
        helpm.add_command(label="Tutorial: Primer circuito", command=lambda: open_tutorial(self, "primer_circuito"))
        helpm.add_command(label="Acerca de", command=lambda: messagebox.showinfo("Acerca de","Sim-Elec (MVP)"))
        m.add_cascade(label="Ayuda", menu=helpm)

        self.config(menu=m)

    @guard
    def open_netlist(self):
        path = filedialog.askopenfilename(filetypes=[("JSON","*.json")])
        if not path: return
        self.netlist_path = path
        self.text_delete()
        self.text.insert("1.0", f"Archivo cargado: {path}\n\n")

    @guard
    def load_template(self, relpath):
        path = os.path.join(os.getcwd(), relpath)
        if not os.path.exists(path):
            messagebox.showerror("Plantilla no encontrada", path)
            return
        self.netlist_path = path
        self.text_delete()
        self.text.insert("1.0", f"Plantilla cargada: {relpath}\n\n")

    @guard
    def run_sim(self):
        if not self.netlist_path:
            messagebox.showwarning("Atención","Carga un netlist JSON primero.")
            return
        nl = load_json(self.netlist_path)
        sol = simulate(nl)
        self.text_delete()
        self.text.insert("end", "=== RESULTADOS ===\n")
        for k,v in sol.node_voltages.items():
            self.text.insert("end", f"{k}: {v:.6f} V\n")
        self.text.insert("end", "\nCorrientes:\n")
        for k,i in sol.branch_currents.items():
            self.text.insert("end", f"{k}: {i:.9f} A\n")
        self.text.insert("end", "\nChecks:\n")
        self.text.insert("end", f"{sol.checks}\n")

    @guard
    def export_pdf(self):
        if not self.netlist_path:
            messagebox.showwarning("Atención","Simula o carga primero un netlist.")
            return
        nl = load_json(self.netlist_path)
        sol = simulate(nl)
        path = filedialog.asksaveasfilename(defaultextension=".pdf")
        if not path: return
        export_solution_pdf(path, nl, sol)
        messagebox.showinfo("OK", f"PDF exportado en:\n{path}")

    @guard
    def open_editor(self):
        if not self.netlist_path:
            messagebox.showwarning("Atención","Carga una plantilla o JSON primero.")
            return
        nl = load_json(self.netlist_path)
        win = tk.Toplevel(self); win.title("Editor de Circuito")
        from .editor import Editor
        ed = Editor(win, nl)
        ed.pack(fill="both", expand=True)
        ed.load_from_netlist()

    def text_delete(self):
        self.text.config(state="normal"); self.text.delete("1.0","end"); self.text.config(state="normal")

if __name__ == "__main__":
    App().mainloop()
