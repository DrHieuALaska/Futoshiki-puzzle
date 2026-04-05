import time
import tracemalloc
from inference.forward_chaining import forward_chaining

def forward_chaining_solve(puzzle, kb):
    start_time = time.time()
    tracemalloc.start()

    N = puzzle.getN()
    facts = set(kb.get_facts())

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
    valid, _, _ = forward_chaining(puzzle, facts, domains)
    if not valid:
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return False, None, None, _make_stats(start_time, peak)   # contradiction in initial KB

    # Step 3: Check if solved
    solution = puzzle.copy()
    is_complete = True

    for (i, j), domain in domains.items():
        if len(domain) == 1:
            solution.grid[i][j] = next(iter(domain))
        else:
            is_complete = False    # FC couldn't determine this cell


    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return is_complete, solution, domains, _make_stats(start_time, peak)

def _make_stats(start_time, peak_bytes):
    return {
        'time_sec':    round(time.time() - start_time, 6),
        'peak_mem_kb': round(peak_bytes / 1024, 2),
    }