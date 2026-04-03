import heapq
import time
import tracemalloc

from inference.forward_chaining import forward_propagate


# ---------------------------------------------------------------------------
# Heuristic
def compute_heuristic(puzzle, domains):
    """
    Admissible heuristic h(s) for A* on a Futoshiki partial assignment.

    Algorithm:
        1. Deep-copy the domains (non-destructive).
        2. Run forward_propagate (AC-3-style arc consistency) on the copy.
        3. If some domain empties, return inf.
        4. Otherwise return the count of cells whose domain has size > 1.

    """
    prop_domains = {k: set(v) for k, v in domains.items()}
    if not forward_propagate(puzzle, prop_domains):
        return float('inf')   # Contradiction → branch is infeasible
    return sum(1 for d in prop_domains.values() if len(d) > 1)


# ---------------------------------------------------------------------------
# AC-3 / domain initialisation helpers
# ---------------------------------------------------------------------------

def _init_domains(puzzle):
    """Build initial domain dict from puzzle clues."""
    domains = {
        (i, j): set(range(1, puzzle.N + 1))
        for i in range(puzzle.N)
        for j in range(puzzle.N)
    }
    for i in range(puzzle.N):
        for j in range(puzzle.N):
            v = puzzle.grid[i][j]
            if v != 0:
                domains[(i, j)] = {v}
    return domains


def _copy_domains(domains):
    return {k: set(v) for k, v in domains.items()}


def _grid_key(puzzle):
    """Hashable representation of the puzzle grid for duplicate detection."""
    return tuple(
        puzzle.grid[i][j]
        for i in range(puzzle.N)
        for j in range(puzzle.N)
    )


# ---------------------------------------------------------------------------
# A* solver
# ---------------------------------------------------------------------------

def solve_astar(puzzle):
    start_time = time.time()
    tracemalloc.start()

    expansions = 0
    generated = 0

    domains_0 = _init_domains(puzzle)

    # Initial arc-consistency pass
    if not forward_propagate(puzzle, domains_0):
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return None, _make_stats(0, 0, start_time, peak)

    # Check if already solved after initial propagation
    if all(len(d) == 1 for d in domains_0.values()):
        solution = _extract_solution(puzzle, domains_0)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return solution, _make_stats(1, 0, start_time, peak)

    g0 = 0
    h0 = compute_heuristic(puzzle, domains_0)
    if h0 == float('inf'):
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return None, _make_stats(0, 0, start_time, peak)

    tie = 0
    open_list = [(g0 + h0, g0, tie, puzzle.copy(), domains_0)]
    tie += 1

    # Closed set: grid states already expanded
    closed = set()

    while open_list:
        f, g, _, curr_puz, curr_dom = heapq.heappop(open_list)

        key = _grid_key(curr_puz)
        if key in closed:
            continue
        closed.add(key)
        expansions += 1

        # Goal test
        if all(len(d) == 1 for d in curr_dom.values()):
            solution = _extract_solution(curr_puz, curr_dom)
            _, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            return solution, _make_stats(expansions, generated, start_time, peak)

        # ------------------------------------------------------------------
        # Select variable (MRV: cell with smallest domain > 1)
        unresolved = [
            (cell, curr_dom[cell])
            for cell in curr_dom
            if len(curr_dom[cell]) > 1
        ]
        if not unresolved:
            continue

        cell, cell_dom = min(unresolved, key=lambda x: len(x[1]))
        ci, cj = cell

        for val in sorted(cell_dom):          # sorted for determinism
            # Quick constraint check before deep copy
            if not curr_puz.is_valid_assignment(ci, cj, val):
                continue

            # Build successor state
            succ_puz = curr_puz.copy()
            succ_puz.grid[ci][cj] = val

            succ_dom = _copy_domains(curr_dom)
            succ_dom[(ci, cj)] = {val}

            # Arc-consistency propagation
            if not forward_propagate(succ_puz, succ_dom):
                continue   # Contradiction: prune this branch

            succ_key = _grid_key(succ_puz)
            if succ_key in closed:
                continue

            # Compute f for successor
            new_g = g + 1            # one explicit branching decision made
            new_h = compute_heuristic(succ_puz, succ_dom)

            if new_h == float('inf'):
                continue   # Infeasible after look-ahead: prune

            new_f = new_g + new_h

            heapq.heappush(open_list, (new_f, new_g, tie, succ_puz, succ_dom))
            tie += 1
            generated += 1

    # Open list exhausted: no solution
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return None, _make_stats(expansions, generated, start_time, peak)


# ---------------------------------------------------------------------------
# Helpers

def _extract_solution(base_puzzle, domains):
    """Build a solved Puzzle from singleton domains."""
    solution = base_puzzle.copy()
    for (i, j), vals in domains.items():
        solution.grid[i][j] = next(iter(vals))
    return solution


def _make_stats(expansions, generated, start_time, peak_bytes):
    return {
        'expansions': expansions,
        'generated': generated,
        'time_sec': round(time.time() - start_time, 6),
        'peak_mem_kb': round(peak_bytes / 1024, 2),
    }
