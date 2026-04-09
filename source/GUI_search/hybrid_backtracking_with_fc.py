import time
import tracemalloc
from inference.forward_chaining import forward_chaining

def solve_hybrid_backtracking_with_fc(puzzle, kb):
    start_time = time.time()
    tracemalloc.start()

    # Create a stats dictionary to track backtracking events
    tracking_stats = {"bt_calls": 0}
    history = []

    N = puzzle.getN()
    facts = set(kb.get_facts())
    rules = kb.get_fol_rules()

    # ── build initial domains ────────────────────────────────
    # Start with full domain {1..N} for every cell
    domains = {(i, j): set(range(1, N + 1))
               for i in range(N) for j in range(N)}

    # Fix domains for cells that already have a Val fact
    for fact in facts:
        if fact[0] == "Val":
            _, i, j, v = fact
            domains[(i, j)] = {v}
    solution = backtrack_with_fc(puzzle, facts, rules, domains, tracking_stats, history)
    
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return solution, _make_stats(start_time, peak, tracking_stats["bt_calls"]), history


def backtrack_with_fc(puzzle, facts, rules, domains, stats, history):
    # 1. Deep Copy before mutating — never touch caller's state
    working_domains = copy_domains(domains)
    working_facts = set(facts)

    # 2. Forward propagation on working copies
    valid, is_complete, working_facts, working_domains = forward_chaining(
        puzzle, working_facts, rules, working_domains
    )

    if not valid:
        return None  # contradiction

    # 2. Check if solved
    if(is_complete):
        solution = puzzle.copy()
        for (i, j), vals in working_domains.items():
            solution.grid[i][j] = next(iter(vals)) # Assign the single value in domain to solution
        return solution
    
    stats["bt_calls"] += 1

    # 3. Choose cell (MRV)
    cell = select_mrv(working_domains)
    i, j = cell

    # 4. Try values
    for val in list(working_domains[cell]):
        # deep copy domains
        new_domains = copy_domains(working_domains)
        new_domains[(i, j)] = {val}
        candidate_facts = working_facts | {("Val", i, j, val)}
        history.append(('assign', i, j, val))

        result = backtrack_with_fc(puzzle, candidate_facts, rules, new_domains, stats, history)
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

def _make_stats(start_time, peak_bytes, bt_count):
    return {
        'time_sec':    round(time.time() - start_time, 6),
        'peak_mem_kb': round(peak_bytes / 1024, 2),
        'bt_fallbacks':    bt_count  # how many times backtracking was invoked after FC couldn't solve
    }