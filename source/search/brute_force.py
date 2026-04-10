import time
import tracemalloc

def brute_force(puzzle):  
    start_time = time.time()
    tracemalloc.start()
    copyPuzzle = puzzle.copy()

    # Backtracking search (recursive)
    def solve(cells, idx):
        if idx == len(cells): return True
        r, c = cells[idx]
        for val in puzzle.domain(): # order: 1,2,...N
            if copyPuzzle.is_valid_assignment(r, c, val):
                copyPuzzle.set(r, c, val)
                if solve(cells, idx+1): return True
                copyPuzzle.unset(r, c)
        return False
    
    # Get list of empty cells of the grid
    empty = copyPuzzle.get_empty_cells()
    result = solve(empty, 0)

    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    if result:
        return copyPuzzle, _make_stats(start_time, peak)
    return None, _make_stats(start_time, peak)

def _make_stats(start_time, peak_bytes):
    return {
        'time_sec':    round(time.time() - start_time, 6),
        'peak_mem_kb': round(peak_bytes / 1024, 2),
    }