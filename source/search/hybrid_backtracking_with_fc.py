from model.constraints import is_valid
from inference.forward_chaining import forward_propagate

def solve_hybrid_backtracking_with_fc(puzzle):
    """
    Entry point
    """
    # Initialize domains
    domains = {
        (i, j): set(range(1, puzzle.N + 1))
        for i in range(puzzle.N)
        for j in range(puzzle.N)
    }

    # Apply given values
    for i in range(puzzle.N):
        for j in range(puzzle.N):
            val = puzzle.grid[i][j]
            if val != 0:
                domains[(i, j)] = {val}

    return backtrack_with_fc(puzzle, domains)


def backtrack_with_fc(puzzle, domains):
    # 1. Forward propagation
    if not forward_propagate(puzzle, domains):
        return None  # contradiction

    # 2. Check if solved
    if all(len(domains[cell]) == 1 for cell in domains):
        solution = puzzle.copy()
        for (i, j), vals in domains.items():
            solution.grid[i][j] = next(iter(vals)) # Assign the single value in domain to solution
        return solution

    # 3. Choose cell (MRV)
    cell = select_mrv(domains)
    i, j = cell

    # 4. Try values
    for val in list(domains[cell]):
        if is_valid(puzzle, i, j, val):
            # deep copy puzzle and domains
            new_puzzle = puzzle.copy()
            new_domains = copy_domains(domains)

            # Assign value
            new_puzzle.grid[i][j] = val
            new_domains[(i, j)] = {val}

            result = backtrack_with_fc(new_puzzle, new_domains)
            if result:
                return result 

    return None

def select_mrv(domains):
    return min(
        (cell for cell in domains if len(domains[cell]) > 1),
        key=lambda c: len(domains[c])
    )

def copy_domains(domains):
    return {k: set(v) for k, v in domains.items()}