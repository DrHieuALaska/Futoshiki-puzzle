import heapq
import time
import tracemalloc

from inference.forward_chaining import forward_propagate


# ---------------------------------------------------------------------------
# Heuristic
# Available heuristic names for A*:
#   - "ac3": run AC-3 on a copied domain map, then count unresolved cells.
#   - "remaining_unassigned_cells": directly count cells with domain size > 1.
#   - "inequality_chains": estimate how many more assignments are needed to
#     touch every still-unresolved horizontal/vertical inequality chain.
def _count_remaining_unassigned_cells(domains):
    """Count cells whose values are not fixed yet."""
    return sum(1 for vals in domains.values() if len(vals) > 1)


def _build_inequality_chains(puzzle):
    """
    Build maximal contiguous horizontal and vertical inequality chains.

    A horizontal chain is a maximal run of non-zero entries in one row of
    `h_constraints`. A vertical chain is defined analogously in
    `v_constraints`.
    """
    horizontal_chains = []
    vertical_chains = []
    cell_to_horizontal = {}
    cell_to_vertical = {}

    for r in range(puzzle.N):
        start = None
        for c in range(puzzle.N - 1):
            has_constraint = puzzle.h_constraints[r][c] != 0

            if has_constraint and start is None:
                start = c

            if start is None:
                continue

            chain_ends_here = (not has_constraint) or (c == puzzle.N - 2)
            if not chain_ends_here:
                continue

            end_edge = c if has_constraint else c - 1
            cells = tuple((r, col) for col in range(start, end_edge + 2))

            chain_id = len(horizontal_chains)
            horizontal_chains.append(cells)
            for cell in cells:
                cell_to_horizontal[cell] = chain_id

            start = None

    for c in range(puzzle.N):
        start = None
        for r in range(puzzle.N - 1):
            has_constraint = puzzle.v_constraints[r][c] != 0

            if has_constraint and start is None:
                start = r

            if start is None:
                continue

            chain_ends_here = (not has_constraint) or (r == puzzle.N - 2)
            if not chain_ends_here:
                continue

            end_edge = r if has_constraint else r - 1
            cells = tuple((row, c) for row in range(start, end_edge + 2))

            chain_id = len(vertical_chains)
            vertical_chains.append(cells)
            for cell in cells:
                cell_to_vertical[cell] = chain_id

            start = None

    return {
        'horizontal_chains': horizontal_chains,
        'vertical_chains': vertical_chains,
        'cell_to_horizontal': cell_to_horizontal,
        'cell_to_vertical': cell_to_vertical,
    }


def _maximum_bipartite_matching(adjacency):
    """DFS-based maximum matching on the chain-intersection graph."""
    matched_right = {}

    def _augment(left_node, seen):
        for right_node in adjacency.get(left_node, ()):
            if right_node in seen:
                continue
            seen.add(right_node)

            if right_node not in matched_right or _augment(matched_right[right_node], seen):
                matched_right[right_node] = left_node
                return True

        return False

    matching_size = 0
    for left_node in adjacency:
        if _augment(left_node, set()):
            matching_size += 1

    return matching_size


def _count_inequality_chain_assignments(domains, chain_data):
    """
    Lower bound the extra assignments needed to touch every unresolved
    inequality chain.

    Each unresolved cell can help at most one horizontal chain and one
    vertical chain, so the minimum cover for the current chain graph is:

        |active_horizontal| + |active_vertical| - maximum_matching
    """
    horizontal_chains = chain_data['horizontal_chains']
    vertical_chains = chain_data['vertical_chains']
    cell_to_horizontal = chain_data['cell_to_horizontal']
    cell_to_vertical = chain_data['cell_to_vertical']

    active_horizontal = {
        chain_id
        for chain_id, cells in enumerate(horizontal_chains)
        if any(len(domains[cell]) > 1 for cell in cells)
    }
    active_vertical = {
        chain_id
        for chain_id, cells in enumerate(vertical_chains)
        if any(len(domains[cell]) > 1 for cell in cells)
    }

    if not active_horizontal and not active_vertical:
        return 0

    adjacency = {chain_id: set() for chain_id in active_horizontal}

    for cell, vals in domains.items():
        if len(vals) <= 1:
            continue

        horizontal_id = cell_to_horizontal.get(cell)
        vertical_id = cell_to_vertical.get(cell)

        if horizontal_id in active_horizontal and vertical_id in active_vertical:
            adjacency[horizontal_id].add(vertical_id)

    matching_size = _maximum_bipartite_matching(adjacency)
    return len(active_horizontal) + len(active_vertical) - matching_size


def compute_heuristic(puzzle, domains, heuristic='ac3', chain_data=None):
    """
    Compute one of the available A* heuristics.

    Supported values:
        - "ac3": keep the original AC-3-style look-ahead heuristic
        - "remaining_unassigned_cells": count unresolved cells directly
        - "inequality_chains": estimate assignments needed to cover all
          unresolved inequality chains
    """
    if heuristic == 'ac3':
        # Original heuristic: propagate first, then measure how many cells
        # are still not forced to a single value.
        prop_domains = {k: set(v) for k, v in domains.items()}
        if not forward_propagate(puzzle, prop_domains):
            return float('inf')   # Contradiction → branch is infeasible
        return _count_remaining_unassigned_cells(prop_domains)

    if any(len(vals) == 0 for vals in domains.values()):
        return float('inf')

    if heuristic == 'remaining_unassigned_cells':
        # Weak but simple lower bound: each unresolved cell may need work.
        return _count_remaining_unassigned_cells(domains)

    if heuristic == 'inequality_chains':
        # Chain-based lower bound: count the least number of extra assignments
        # needed to hit all unresolved inequality chains.
        if chain_data is None:
            chain_data = _build_inequality_chains(puzzle)
        return _count_inequality_chain_assignments(domains, chain_data)

    raise ValueError(
        f"Unknown A* heuristic '{heuristic}'. "
        "Choose from: ac3, remaining_unassigned_cells, inequality_chains"
    )


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

def solve_astar(puzzle, heuristic='ac3'):
    start_time = time.time()
    tracemalloc.start()

    expansions = 0
    generated = 0
    chain_data = None

    # Only the chain heuristic needs precomputed chain metadata.
    if heuristic == 'inequality_chains':
        chain_data = _build_inequality_chains(puzzle)

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
    h0 = compute_heuristic(puzzle, domains_0, heuristic, chain_data)
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
            new_h = compute_heuristic(succ_puz, succ_dom, heuristic, chain_data)

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
