import heapq
import time
import tracemalloc
from collections import deque

from inference.forward_chaining import forward_chaining


# -----------------------------------------------------------------------------
# Heuristic 1 — Remaining Unassigned Cells
# -----------------------------------------------------------------------------

def _h_remaining_cells(domains):
    """
    h(n) = number of cells whose domain still has more than one candidate.
    Admissible: each such cell needs at least one more assignment, so this
    never overestimates the true remaining cost.
    """
    return sum(1 for vals in domains.values() if len(vals) > 1)


# -----------------------------------------------------------------------------
# Heuristic 2 — Inequality Chain Coverage  (bipartite matching lower bound)
# -----------------------------------------------------------------------------

def _build_inequality_chains(puzzle):
    """
    Scan all rows and columns and collect every maximal contiguous sequence
    of cells that are linked by at least one inequality constraint edge.

    Example row:  (0,0) < (0,1) > (0,2)   [no edge]   (0,3) < (0,4)
    → two chains: ((0,0),(0,1),(0,2))  and  ((0,3),(0,4))

    Called ONCE before the search loop and cached in chain_data.
    """
    horizontal_chains  = []
    vertical_chains    = []
    cell_to_horizontal = {}
    cell_to_vertical   = {}

    # ── horizontal chains ────────────────────────────────────────────────────
    for r in range(puzzle.N):
        start = None
        for c in range(puzzle.N - 1):
            has_edge = puzzle.h_constraints[r][c] != 0
            if has_edge and start is None:
                start = c                         # begin a new chain at col c
            if start is None:
                continue
            ends = (not has_edge) or (c == puzzle.N - 2)
            if not ends:
                continue
            last_edge  = c if has_edge else c - 1
            cells      = tuple((r, col) for col in range(start, last_edge + 2))
            cid        = len(horizontal_chains)
            horizontal_chains.append(cells)
            for cell in cells:
                cell_to_horizontal[cell] = cid
            start = None

    # ── vertical chains ───────────────────────────────────────────────────────
    for c in range(puzzle.N):
        start = None
        for r in range(puzzle.N - 1):
            has_edge = puzzle.v_constraints[r][c] != 0
            if has_edge and start is None:
                start = r
            if start is None:
                continue
            ends = (not has_edge) or (r == puzzle.N - 2)
            if not ends:
                continue
            last_edge = r if has_edge else r - 1
            cells     = tuple((row, c) for row in range(start, last_edge + 2))
            cid       = len(vertical_chains)
            vertical_chains.append(cells)
            for cell in cells:
                cell_to_vertical[cell] = cid
            start = None

    return {
        'horizontal_chains':  horizontal_chains,
        'vertical_chains':    vertical_chains,
        'cell_to_horizontal': cell_to_horizontal,
        'cell_to_vertical':   cell_to_vertical,
    }


def _maximum_bipartite_matching(adjacency):
    """
    DFS-based augmenting-path algorithm (Hungarian / Hopcroft-Karp style).
    adjacency  : dict  left_node → set of right_nodes
    Returns the size of the maximum matching.
    """
    matched_right = {}

    def _augment(left, seen):
        for right in adjacency.get(left, ()):
            if right in seen:
                continue
            seen.add(right)
            if right not in matched_right or _augment(matched_right[right], seen):
                matched_right[right] = left
                return True
        return False

    size = 0
    for left in adjacency:
        if _augment(left, set()):
            size += 1
    return size


def _h_inequality_chains(domains, chain_data):
    """
    h(n) = |active_horizontal| + |active_vertical| − max_matching
    """
    h_chains  = chain_data['horizontal_chains']
    v_chains  = chain_data['vertical_chains']
    cell_to_h = chain_data['cell_to_horizontal']
    cell_to_v = chain_data['cell_to_vertical']

    # active = chains that still contain at least one unresolved cell
    active_h = {
        cid for cid, cells in enumerate(h_chains)
        if any(len(domains[cell]) > 1 for cell in cells)
    }
    active_v = {
        cid for cid, cells in enumerate(v_chains)
        if any(len(domains[cell]) > 1 for cell in cells)
    }

    if not active_h and not active_v:
        return 0

    # Build bipartite graph: H-chain ↔ V-chain if a shared unresolved cell exists
    adj = {cid: set() for cid in active_h}
    for cell, vals in domains.items():
        if len(vals) <= 1:
            continue
        h_id = cell_to_h.get(cell)
        v_id = cell_to_v.get(cell)
        if h_id in active_h and v_id in active_v:
            adj[h_id].add(v_id)

    matching = _maximum_bipartite_matching(adj)
    return len(active_h) + len(active_v) - matching


# -----------------------------------------------------------------------------
# Heuristic 3 — Combined  (max of the two pure heuristics above)
# -----------------------------------------------------------------------------

def _h_combined(domains, chain_data):
    """
    h(n) = max( remaining_cells,  inequality_chains )

    Taking the maximum of two admissible heuristics is still admissible
    (both are lower bounds, so the larger one is also a lower bound and
    is strictly tighter).

    This gives the best node ordering of the three heuristics without
    any lookahead cost (no domain copies, no arc propagation).
    """
    h1 = _h_remaining_cells(domains)
    h2 = _h_inequality_chains(domains, chain_data)
    return max(h1, h2)



def _compute_heuristic(domains, heuristic, chain_data):
    """
    heuristic ∈ {'remaining_cells', 'inequality_chains', 'combined'}
    """
    if any(len(v) == 0 for v in domains.values()):
        return float('inf')

    if heuristic == 'remaining_cells':
        return _h_remaining_cells(domains)

    if heuristic == 'inequality_chains':
        return _h_inequality_chains(domains, chain_data)

    if heuristic == 'combined':
        return _h_combined(domains, chain_data)

    raise ValueError(
        f"Unknown heuristic '{heuristic}'. "
        "Choose from: remaining_cells, inequality_chains, combined"
    )


# =============================================================================
# SECTION 2 — PRUNING METHODS
# =============================================================================

# -----------------------------------------------------------------------------
# Pruning method 1 — Forward Chaining  (wraps the existing FC engine)
# -----------------------------------------------------------------------------

def _prune_fc(facts, rules, domains):
    """
    Run the FOL forward-chaining engine on the current (facts, domains).
    Returns
    -------
    is_valid   : False if any domain became empty (contradiction)
    is_done    : True  if every domain is now a singleton (puzzle solved)
    facts      : updated fact set
    domains    : updated domain dict
    """
    is_valid, is_done, facts, domains = forward_chaining(facts, rules, domains)
    return is_valid, is_done, facts, domains


# -----------------------------------------------------------------------------
# Pruning method 2 — AC-3  (arc consistency, domain-level propagation)
# -----------------------------------------------------------------------------

def _build_ac3_arcs(puzzle):
    """
    Build the complete arc list and reverse-neighbor index for AC-3.
    Called ONCE per puzzle and cached — never rebuilt inside the search loop.

    An arc  (Xi, Xj, ctype)  means:
        "every value in Xi must have at least one compatible value in Xj"

    ctype ∈ {'neq', 'lt', 'gt'}
        'neq'  Xi ≠ Xj   (row / column uniqueness)
        'lt'   Xi < Xj   (inequality, Xi's side)
        'gt'   Xi > Xj   (inequality, Xi's side)

    neighbors_of[cell] lists every arc (Xi, Xj, ctype) where Xj == cell.
    When Xj's domain shrinks, all arcs in neighbors_of[Xj] must be
    re-checked because Xi may have lost support.
    """
    N    = puzzle.N
    arcs = []

    for i in range(N):
        for j in range(N):
            # row uniqueness — both directions for every column pair
            for jj in range(j + 1, N):
                arcs.append(((i, j),  (i, jj), 'neq'))
                arcs.append(((i, jj), (i, j),  'neq'))
            # column uniqueness — both directions for every row pair
            for ii in range(i + 1, N):
                arcs.append(((i, j),  (ii, j), 'neq'))
                arcs.append(((ii, j), (i, j),  'neq'))
            # horizontal inequality
            if j < N - 1:
                c = puzzle.h_constraints[i][j]
                if c == 1:      # (i,j) < (i,j+1)
                    arcs.append(((i, j),   (i, j+1), 'lt'))
                    arcs.append(((i, j+1), (i, j),   'gt'))
                elif c == -1:   # (i,j) > (i,j+1)
                    arcs.append(((i, j),   (i, j+1), 'gt'))
                    arcs.append(((i, j+1), (i, j),   'lt'))
            # vertical inequality
            if i < N - 1:
                c = puzzle.v_constraints[i][j]
                if c == 1:      # (i,j) < (i+1,j)
                    arcs.append(((i, j),   (i+1, j), 'lt'))
                    arcs.append(((i+1, j), (i, j),   'gt'))
                elif c == -1:   # (i,j) > (i+1,j)
                    arcs.append(((i, j),   (i+1, j), 'gt'))
                    arcs.append(((i+1, j), (i, j),   'lt'))

    # reverse index: Xj → list of arcs that need re-checking when Xj shrinks
    neighbors_of = {(i, j): [] for i in range(N) for j in range(N)}
    for arc in arcs:
        _, xj, _ = arc
        neighbors_of[xj].append(arc)

    return arcs, neighbors_of


def _prune_ac3(domains, arcs, neighbors_of):
    def _has_support(val, dom_xj, ctype):
        if ctype == 'neq': return any(v != val for v in dom_xj)
        if ctype == 'lt':  return any(v >  val for v in dom_xj)
        if ctype == 'gt':  return any(v <  val for v in dom_xj)

    # work on a copy so the caller's domains are never mutated
    dom      = {cell: set(vals) for cell, vals in domains.items()}
    in_queue = set(arcs)
    queue    = deque(arcs)

    while queue:
        xi, xj, ctype = queue.popleft()
        in_queue.discard((xi, xj, ctype))

        before  = len(dom[xi])
        dom[xi] = {v for v in dom[xi] if _has_support(v, dom[xj], ctype)}

        if len(dom[xi]) == before:
            continue                         # no change → nothing to propagate

        if len(dom[xi]) == 0:
            return False, False, dom         # empty domain → contradiction

        # Xi shrank → re-check all arcs whose source depends on Xi
        for arc in neighbors_of[xi]:
            if arc not in in_queue:
                queue.append(arc)
                in_queue.add(arc)

    is_done = all(len(v) == 1 for v in dom.values())
    return True, is_done, dom


# =============================================================================
# SECTION 3 — SHARED HELPERS
# =============================================================================

def _init_domains(puzzle):
    """Initial domain dict: pre-filled cells → singleton, empty → {1..N}."""
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
    """Flat tuple of the grid — used as a hashable closed-set key."""
    return tuple(
        puzzle.grid[i][j]
        for i in range(puzzle.N)
        for j in range(puzzle.N)
    )


def _extract_solution(base_puzzle, domains):
    """Build a solved Puzzle object from singleton domains."""
    sol = base_puzzle.copy()
    for (i, j), vals in domains.items():
        sol.grid[i][j] = next(iter(vals))
    return sol


def _make_stats(expansions, generated, start_time, peak_bytes):
    return {
        'expansions':  expansions,
        'generated':   generated,
        'time_sec':    round(time.time() - start_time, 6),
        'peak_mem_kb': round(peak_bytes / 1024, 2),
    }


# =============================================================================
# SECTION 4 — A* SOLVER
# =============================================================================

def solve_astar(puzzle, kb, heuristic='combined', pruning='fc'):
    print(
        f"[A*] heuristic='{heuristic}'  pruning='{pruning}'  "
        f"size={puzzle.N}x{puzzle.N}"
    )

    start_time = time.time()
    tracemalloc.start()

    expansions = 0
    generated  = 0

    # chain_data is needed by both 'inequality_chains' and 'combined'
    chain_data = (
        _build_inequality_chains(puzzle)
        if heuristic in ('inequality_chains', 'combined')
        else None
    )
    # ac3_arcs / ac3_neighbors only needed when pruning == 'ac3'
    ac3_arcs, ac3_neighbors = (
        _build_ac3_arcs(puzzle) if pruning == 'ac3' else (None, None)
    )

    # ── initial domain setup ──────────────────────────────────────────────────
    domains_0 = _init_domains(puzzle)
    facts      = set(kb.get_facts())
    rules      = kb.get_fol_rules()

    # ── initial pruning pass (before any search) ──────────────────────────────
    # Propagate all given clues through the chosen pruning method.
    # This often resolves many cells before A* even starts.
    if pruning == 'fc':
        is_valid, is_done, facts, domains_0 = _prune_fc(facts, rules, domains_0)
    else:  # 'ac3'
        is_valid, is_done, domains_0 = _prune_ac3(domains_0, ac3_arcs, ac3_neighbors)

    if not is_valid:
        print("[A*] Contradiction in initial state — no solution.")
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return None, _make_stats(0, 0, start_time, peak)

    if is_done:
        print("[A*] Solved by initial propagation — no search needed.")
        solution = _extract_solution(puzzle, domains_0)
        _, peak  = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return solution, _make_stats(1, 0, start_time, peak)

    # ── initial heuristic value ───────────────────────────────────────────────
    h0 = _compute_heuristic(domains_0, heuristic, chain_data)
    if h0 == float('inf'):
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return None, _make_stats(0, 0, start_time, peak)

    # ── open list: (f, g, tie, puzzle, facts, domains) ───────────────────────
    # tie-breaker prevents Python comparing puzzle/dict objects on f/g ties
    tie       = 0
    open_list = [(h0, 0, tie, puzzle.copy(), facts, domains_0)]
    tie      += 1
    closed    = set()

    # =========================================================================
    # A* main loop
    # =========================================================================
    while open_list:
        f, g, _, curr_puz, curr_facts, curr_dom = heapq.heappop(open_list)

        # ── duplicate-state check ─────────────────────────────────────────────
        key = _grid_key(curr_puz)
        if key in closed:
            continue
        closed.add(key)
        expansions += 1

        # ── goal check ────────────────────────────────────────────────────────
        if all(len(d) == 1 for d in curr_dom.values()):
            solution = _extract_solution(curr_puz, curr_dom)
            _, peak  = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            return solution, _make_stats(expansions, generated, start_time, peak)

        # ── MRV variable selection ────────────────────────────────────────────
        best_cell, best_size = None, float('inf')
        for cell, vals in curr_dom.items():
            s = len(vals)
            if 1 < s < best_size:
                best_size, best_cell = s, cell
                if s == 2:
                    break           # can't do better than binary choice

        if best_cell is None:
            continue                # safety: shouldn't happen after goal check

        ci, cj   = best_cell
        cell_dom = curr_dom[best_cell]

        # ── expand: try every candidate value for the chosen cell ────────────
        for val in sorted(cell_dom):    # sorted → deterministic expansion order

            succ_dom           = _copy_domains(curr_dom)
            succ_dom[(ci, cj)] = {val}

            # prunning step
            if pruning == 'fc':
                succ_facts = curr_facts | {("Val", ci, cj, val)}
                is_valid, is_done, succ_facts, succ_dom = _prune_fc(
                    succ_facts, rules, succ_dom
                )
            else:  # 'ac3'
                succ_facts = curr_facts | {("Val", ci, cj, val)}
                is_valid, is_done, succ_dom = _prune_ac3(
                    succ_dom, ac3_arcs, ac3_neighbors
                )

            if not is_valid: # contradiction -> skip this successor
                continue           

            succ_puz = curr_puz.copy()
            for (r, c), vals in succ_dom.items():
                succ_puz.grid[r][c] = next(iter(vals)) if len(vals) == 1 else 0

            if is_done:
                solution = _extract_solution(succ_puz, succ_dom)
                _, peak  = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                return solution, _make_stats(expansions + 1, generated + 1, start_time, peak)

            succ_key = _grid_key(succ_puz)
            if succ_key in closed:
                continue
            
            # update heuristic
            new_g = g + 1
            new_h = _compute_heuristic(succ_dom, heuristic, chain_data)
            if new_h == float('inf'):
                continue            

            if all(len(v) == 1 for v in succ_dom.values()):
                solution = _extract_solution(succ_puz, succ_dom)
                _, peak  = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                return solution, _make_stats(expansions + 1, generated + 1, start_time, peak)

            heapq.heappush(
                open_list,
                (new_g + new_h, new_g, tie, succ_puz, succ_facts, succ_dom)
            )
            tie       += 1
            generated += 1

    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return None, _make_stats(expansions, generated, start_time, peak)