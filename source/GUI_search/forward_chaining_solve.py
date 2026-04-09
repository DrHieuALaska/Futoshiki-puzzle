import time
import tracemalloc
from inference.forward_chaining import forward_chaining

def forward_chaining_solve(puzzle, kb):
    start_time = time.time()
    tracemalloc.start()

    N = puzzle.getN()
    facts = set(kb.get_facts())
    rules = kb.get_fol_rules()
    history = []

    # ── Step 1: build initial domains ────────────────────────────────
    # Start with full domain {1..N} for every cell
    domains = {(i, j): set(range(1, N + 1))
               for i in range(N) for j in range(N)}

    # Fix domains for cells that already have a Val fact
    for fact in facts:
        if fact[0] == "Val":
            _, i, j, v = fact
            domains[(i, j)] = {v}

    # Step 2: Forward chaining solve
    valid, is_complete, _, _ = forward_chaining(puzzle, facts, rules, domains)
    if not valid:
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return False, None, None, _make_stats(start_time, peak), history   # contradiction in initial KB

    # Step 3: Check if solved
    solution = puzzle.copy()

    if(not is_complete):
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return False, None, None, _make_stats(start_time, peak), history   # not fully solved
    
    # Fill in solution grid from domains (each should have exactly 1 value)
    for (i, j), domain in domains.items():
        if len(domain) == 1:
            solution.grid[i][j] = next(iter(domain))
            history.append(('assign', i, j, next(iter(domain))))


    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return is_complete, solution, domains, _make_stats(start_time, peak), history

def _make_stats(start_time, peak_bytes):
    return {
        'time_sec':    round(time.time() - start_time, 6),
        'peak_mem_kb': round(peak_bytes / 1024, 2),
    }