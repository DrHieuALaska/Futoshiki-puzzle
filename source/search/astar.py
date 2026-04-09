import heapq
import time
import tracemalloc

from inference.forward_chaining import forward_chaining


# ---------------------------------------------------------------------------
# Heuristic helpers

def _count_remaining_unassigned_cells(domains):
    """Count cells whose values are not fixed yet."""
    return sum(1 for vals in domains.values() if len(vals) > 1)


def _build_inequality_chains(puzzle):
    """
    Build maximal contiguous horizontal and vertical inequality chains.
    Called once before the search loop; result is reused across all nodes.
    """
    horizontal_chains  = []
    vertical_chains    = []
    cell_to_horizontal = {}
    cell_to_vertical   = {}

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
        'horizontal_chains':  horizontal_chains,
        'vertical_chains':    vertical_chains,
        'cell_to_horizontal': cell_to_horizontal,
        'cell_to_vertical':   cell_to_vertical,
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
    Lower bound: minimum assignments needed to touch every unresolved chain.

        |active_horizontal| + |active_vertical| - maximum_matching
    """
    horizontal_chains  = chain_data['horizontal_chains']
    vertical_chains    = chain_data['vertical_chains']
    cell_to_horizontal = chain_data['cell_to_horizontal']
    cell_to_vertical   = chain_data['cell_to_vertical']

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
        h_id = cell_to_horizontal.get(cell)
        v_id = cell_to_vertical.get(cell)
        if h_id in active_horizontal and v_id in active_vertical:
            adjacency[h_id].add(v_id)

    matching_size = _maximum_bipartite_matching(adjacency)
    return len(active_horizontal) + len(active_vertical) - matching_size


def _compute_heuristic(puzzle, domains, heuristic, chain_data):
    """
    Compute heuristic on domains that are already forward-propagated.
    """
    if heuristic == 'ac3':
        return _count_remaining_unassigned_cells(domains)

    if any(len(vals) == 0 for vals in domains.values()):
        return float('inf')

    if heuristic == 'remaining_unassigned_cells':
        return _count_remaining_unassigned_cells(domains)

    if heuristic == 'inequality_chains':
        if chain_data is None:
            chain_data = _build_inequality_chains(puzzle)
        return _count_inequality_chain_assignments(domains, chain_data)

    raise ValueError(
        f"Unknown A* heuristic '{heuristic}'. "
        "Choose from: ac3, remaining_unassigned_cells, inequality_chains"
    )


# ---------------------------------------------------------------------------
# Helpers

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
    """Hashable state key from the puzzle grid."""
    return tuple(
        puzzle.grid[i][j]
        for i in range(puzzle.N)
        for j in range(puzzle.N)
    )


# ---------------------------------------------------------------------------
# A* solver

def solve_astar(puzzle, kb, heuristic='ac3'):
    start_time = time.time()
    tracemalloc.start()


    expansions = 0
    generated  = 0

    # Chain metadata depends only on puzzle structure — precompute once.
    chain_data = _build_inequality_chains(puzzle) if heuristic == 'inequality_chains' else None

    domains_0 = _init_domains(puzzle)

    # Initial forward propagation on the initial KB facts, before A* loop.
    facts = set(kb.get_facts())
    rules = kb.get_fol_rules()

    valid, is_finished, facts, domains_0 = forward_chaining(puzzle, facts, rules, domains_0)

    if not valid:
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return None, _make_stats(0, 0, start_time, peak)

    # Already solved after initial propagation?
    if(is_finished):
        solution = _extract_solution(puzzle, domains_0)
        _, peak  = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return solution, _make_stats(1, 0, start_time, peak)

    # OPT #3: domains_0 already propagated, no second pass needed.
    h0 = _compute_heuristic(puzzle, domains_0, heuristic, chain_data)
    if h0 == float('inf'):
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return None, _make_stats(0, 0, start_time, peak)

    tie       = 0
    open_list = [(h0, 0, tie, puzzle.copy(), facts, domains_0)]
    tie      += 1

    closed = set()

    while open_list:
        f, g, _, curr_puz, curr_facts, curr_dom = heapq.heappop(open_list)

        key = _grid_key(curr_puz)
        if key in closed:
            continue
        closed.add(key)
        expansions += 1

        # Goal check
        if all(len(d) == 1 for d in curr_dom.values()):
            solution = _extract_solution(curr_puz, curr_dom)
            _, peak  = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            return solution, _make_stats(expansions, generated, start_time, peak)

        # OPT #6: MRV with early exit at domain size 2
        best_cell, best_size = None, float('inf')
        for cell, vals in curr_dom.items():
            s = len(vals)
            if 1 < s < best_size:
                best_size, best_cell = s, cell
                if s == 2:
                    break

        if best_cell is None:
            continue

        ci, cj   = best_cell
        cell_dom = curr_dom[best_cell]

        for val in sorted(cell_dom):   # sorted for determinism

            # OPT #4: skip redundant is_valid_assignment — forward_propagate
            # catches all contradictions including single-cell violations.

            succ_dom           = _copy_domains(curr_dom)
            succ_dom[(ci, cj)] = {val}
            succ_facts = curr_facts | {("Val", ci, cj, val)}
            
            is_valid, is_finished, succ_facts, succ_dom = forward_chaining(curr_puz, succ_facts, rules, succ_dom)

            if(not is_valid):
                continue   # contradiction found → skip successor

            succ_puz = curr_puz.copy()
            for (r, c), vals in succ_dom.items():
                if len(vals) == 1:
                    succ_puz.grid[r][c] = next(iter(vals))
                else:
                    succ_puz.grid[r][c] = 0    # still unresolved

            if is_finished:
                solution = _extract_solution(succ_puz, succ_dom)
                _, peak  = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                return solution, _make_stats(expansions + 1, generated + 1, start_time, peak)

            succ_key = _grid_key(succ_puz)
            if succ_key in closed:
                continue

            new_g = g + 1

            # OPT #3: heuristic on already-propagated domains.
            new_h = _compute_heuristic(succ_puz, succ_dom, heuristic, chain_data)
            if new_h == float('inf'):
                continue   # infeasible: prune

            # Safe early exit only when every domain is already singleton.
            # A heuristic value of 0 does not necessarily mean the puzzle is
            # solved, especially for inequality_chains on boards with few or
            # no inequality constraints.
            if all(len(vals) == 1 for vals in succ_dom.values()):
                solution = _extract_solution(succ_puz, succ_dom)
                _, peak  = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                return solution, _make_stats(expansions + 1, generated + 1, start_time, peak)

            heapq.heappush(open_list, (new_g + new_h, new_g, tie, succ_puz, succ_facts, succ_dom))
            tie       += 1
            generated += 1

    # Open list exhausted: no solution
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    print("Open list exhausted. No solution found.")
    return None, _make_stats(expansions, generated, start_time, peak)


def _extract_solution(base_puzzle, domains):
    """Build a solved Puzzle from singleton domains."""
    solution = base_puzzle.copy()
    for (i, j), vals in domains.items():
        solution.grid[i][j] = next(iter(vals))
    return solution


def _make_stats(expansions, generated, start_time, peak_bytes):
    return {
        'expansions':  expansions,
        'generated':   generated,
        'time_sec':    round(time.time() - start_time, 6),
        'peak_mem_kb': round(peak_bytes / 1024, 2),
    }
