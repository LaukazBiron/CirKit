import numpy as np

class LinearSolver:
    def solve(self, A, b):
        return np.linalg.solve(A, b)
