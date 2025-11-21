# src/ui/tk/errors.py
from tkinter import messagebox

def guard(action):
    def wrapper(*args, **kwargs):
        try:
            return action(*args, **kwargs)
        except Exception as e:
            messagebox.showerror("Error", str(e))
    return wrapper
