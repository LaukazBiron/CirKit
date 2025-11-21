import tkinter as tk

TUTORIALS = {
"bienvenida": """# Bienvenido a Sim-Elec
- Use **Plantillas** para cargar un circuito base.
- Luego vaya a **Simulación → Simular** para calcular V e I.
- **Archivo → Exportar PDF** generará un reporte con netlist y resultados.
- Cargue sus propios JSON desde **Archivo → Abrir netlist...**
""",
"primer_circuito": """# Primer circuito (Divisor)
1) Cargue 'Divisor R (VR)' desde Plantillas
2) Simule (menú Simulación)
3) Vea voltajes y corrientes resultantes; exporte a PDF.
""",
"diodo_ideal": """# Diodo ideal
- ON: ánodo al nodo alto y cátodo a GND → conduce.
- OFF: invierta las terminales o baje el voltaje → no conduce.
"""
}

def open_tutorial(parent, key="bienvenida"):
    win = tk.Toplevel(parent); win.title("Tutorial")
    text = tk.Text(win, wrap="word")
    text.insert("1.0", TUTORIALS.get(key, ""))
    text.config(state="disabled"); text.pack(fill="both", expand=True)
