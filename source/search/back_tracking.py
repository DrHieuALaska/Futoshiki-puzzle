import time
import tracemalloc
def solve_backtracking(puzzle):
    """
    Entry function
    """
    start_time = time.time()
    tracemalloc.start()

    copyPuzzle = puzzle.copy()
    solution = backtrack(copyPuzzle)

    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    return solution, _make_stats(start_time, peak)

# Helper functions for backtracking search
def count_valid_options(puzzle, r, c):
    count = 0
    for val in puzzle.domain():
        if puzzle.is_valid_assignment(r, c, val):
            count += 1
    return count

def select_unassigned_cell(puzzle):
    """
    MRV heuristic:
    Choose cell with fewest valid values
    """
    best_cell = None
    min_options = float('inf')

    for r in range(puzzle.N):
        for c in range(puzzle.N):
            if puzzle.grid[r][c] == 0:
                options = count_valid_options(puzzle, r, c)

                if options < min_options:
                    min_options = options
                    best_cell = (r, c)

    return best_cell

# Backtracking search
def backtrack(puzzle):
    # stop if filled
    if puzzle.is_filled():
        return puzzle
    
    # Choose next empty cell
    r, c = select_unassigned_cell(puzzle)

    # Try all values
    for val in puzzle.domain():
        if puzzle.is_valid_assignment(r, c, val):
            puzzle.set(r, c, val)

            result = backtrack(puzzle)
            if result is not None:
                return result

            # Undo (backtrack)
            puzzle.set(r, c, 0)

    return None

def _make_stats(start_time, peak_bytes):
    return {
        'time_sec':    round(time.time() - start_time, 6),
        'peak_mem_kb': round(peak_bytes / 1024, 2),
    }