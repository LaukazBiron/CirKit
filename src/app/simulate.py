from ..analysis.tableau import build_system
from ..analysis.solver import LinearSolver
from ..analysis.checks import run_checks
from ..analysis.results import Solution
from .validation import validate

def simulate(nl) -> Solution:
    validate(nl)
    A, b, meta = build_system(nl)
    x = LinearSolver().solve(A, b)
    sol = meta.reconstruct_solution(x)
    sol.checks = run_checks(nl, sol)
    return sol
