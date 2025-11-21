# -*- coding: utf-8 -*-
import sys, pathlib, importlib.util

HERE = pathlib.Path(__file__).resolve()
ROOT = HERE.parents[3] if len(HERE.parents) >= 4 else HERE.parent
# Si está congelado por PyInstaller, _MEIPASS apunta al bundle temporal
BASE = pathlib.Path(getattr(sys, "_MEIPASS", ROOT))

INTERFAZ_PATH = BASE / "src" / "ui" / "kivy" / "InterfazMain.py"

def import_from_file(mod_name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(mod_name, str(path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[mod_name] = mod
    spec.loader.exec_module(mod)  # type: ignore
    return mod

InterfazMain = import_from_file("InterfazMain", INTERFAZ_PATH)
CirKitApp = InterfazMain.CirKitApp

if __name__ == "__main__":
    CirKitApp().run()
