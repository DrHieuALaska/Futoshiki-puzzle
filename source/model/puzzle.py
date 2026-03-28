from model.constraints import is_valid

class Puzzle:
    def __init__(self, N, grid, h_constraints, v_constraints):
        self.N = N
        self.grid = grid
        self.h_constraints = h_constraints
        self.v_constraints = v_constraints

    def is_filled(self):
        """Check if puzzle is completely filled"""
        for row in self.grid:
            if 0 in row:
                return False
        return True

    def get(self, r, c):
        return self.grid[r][c]

    def set(self, r, c, val):
        self.grid[r][c] = val

    def unset(self, r, c):
        self.grid[r][c] = 0

    def copy(self):
        """Deep copy"""
        new_grid = [row[:] for row in self.grid]

        new_h_constraints = [row[:] for row in self.h_constraints]

        new_v_constraints = [row[:] for row in self.v_constraints]

        return Puzzle( 
            self.N,
            new_grid,
            new_h_constraints,
            new_v_constraints
        )

    def get_empty_cells(self):
        """Return list of (r, c) that are empty"""
        empty = []
        for i in range(self.N):
            for j in range(self.N):
                if self.grid[i][j] == 0:
                    empty.append((i, j))
        return empty

    def domain(self):
        """Return possible values"""
        return list(range(1, self.N + 1))
    
    def is_valid_assignment(self, r, c, val):
        return is_valid(self, r, c, val)

    # Debug / display
    def __str__(self):
        return "\n".join(
            [" ".join(map(str, row)) for row in self.grid]
        )