import sys
from .serialization import load_json
from .simulate import simulate

def main():
    if len(sys.argv) < 2:
        print("Uso: python -m app.run_cli <netlist.json>")
        sys.exit(1)
    nl = load_json(sys.argv[1])
    sol = simulate(nl)
    print("Voltajes nodales:")
    for k,v in sol.node_voltages.items():
        print(f"  {k}: {v:.6f} V")
    print("Corrientes de ramas:")
    for k,i in sol.branch_currents.items():
        print(f"  {k}: {i:.9f} A")
    print("Checks:", sol.checks)

if __name__ == "__main__":
    main()
