from inference.backward_chaining import _sld_search
import time
import tracemalloc
"""
Backward Chaining (SLD Resolution) solver for Futoshiki.

Strategy:
  - GOAL: prove Val(i, j, v) for every empty cell
  - To prove Val(i, j, v) is safe:
      Tentatively add it, then try to derive FALSE via rules
      If FALSE is NOT derivable -> v is consistent -> accept it
  - Uses depth-first SLD resolution (Prolog-style)
"""


# ─────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────

def backward_chaining_solve(puzzle, kb):
    """
    Entry function
    """
    start_time = time.time()
    tracemalloc.start()

    copyPuzzle = puzzle.copy()
    solution = solve_backward_chaining(copyPuzzle, kb)

    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    return solution, _make_stats(start_time, peak)

def solve_backward_chaining(puzzle, kb):
    """
    Entry point. Extracts facts/rules and starts recursive SLD search.
    """
    N = puzzle.getN()
    facts = set(kb.get_facts())    
    rules = kb.get_fol_rules()      

    # Build initial assignment from Val facts already known (given clues)
    assignment = {}
    for fact in facts:
        if fact[0] == "Val":
            _, i, j, v = fact
            assignment[(i, j)] = v

    result = _sld_search(puzzle, N, facts, rules, assignment)
    if result is None:
        return None

    solution = puzzle.copy()
    for (i, j), v in result.items():
        solution.grid[i][j] = v
    return solution

def _make_stats(start_time, peak_bytes):
    return {
        'time_sec':    round(time.time() - start_time, 6),
        'peak_mem_kb': round(peak_bytes / 1024, 2),
    }