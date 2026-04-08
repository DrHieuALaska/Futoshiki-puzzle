import time
import tracemalloc


def resolution_solver(puzzle, kb):
    """
    Resolution refutation solver.

    To prove the puzzle has a solution:
      1. Generate all possible Val(i,j,v) assignments as candidate clauses
      2. For each empty cell, find a consistent value via refutation:
           - Add ¬Val(i,j,v) to clause set
           - If resolution derives empty clause → contradiction
           → ¬Val(i,j,v) is unsatisfiable → Val(i,j,v) must be true
      3. Assign and propagate

    Returns: solved puzzle or None
    """
    start_time = time.time()
    tracemalloc.start()

    N       = puzzle.getN()
    clauses = [set(c) for c in kb.get_clauses()]   # working clause set

    solution = puzzle.copy()
    assignment = {}

    # Extract already-known values from unit clauses
    for clause in clauses:
        if len(clause) == 1:
            lit = next(iter(clause))
            if isinstance(lit, tuple) and lit[0] == "Val":
                _, i, j, v = lit
                assignment[(i, j)] = v

    # Solve each empty cell
    for i in range(N):
        for j in range(N):
            if (i, j) in assignment:
                solution.grid[i][j] = assignment[(i, j)]
                continue

            found = False
            for v in range(1, N + 1):
                # Refutation: assume ¬Val(i,j,v) and try to derive FALSE
                # If we derive empty clause → Val(i,j,v) must be true
                neg_clause = {("NOT", ("Val", i, j, v))}
                test_clauses = clauses + [neg_clause]

                if _resolve_to_empty(test_clauses):
                    # Contradiction found → Val(i,j,v) is proven
                    assignment[(i, j)] = v
                    solution.grid[i][j] = v

                    # Add Val(i,j,v) as unit clause for future cells
                    clauses.append({("Val", i, j, v)})
                    # Add ¬Val(i,j,w) for all w≠v
                    for w in range(1, N + 1):
                        if w != v:
                            clauses.append({("NOT", ("Val", i, j, w))})
                    found = True
                    break

            if not found:
                _, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                return None, _make_stats(start_time, peak)

    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return solution, _make_stats(start_time, peak)


def _resolve_to_empty(clauses):
    """
    Core resolution engine.
    Repeatedly resolve pairs of clauses until:
      - Empty clause derived → return True (contradiction)
      - No new clauses possible → return False (consistent)

    Resolution rule:
      {A ∨ P} and {B ∨ ¬P}  →  {A ∨ B}   (resolvent)
      If A = B = ∅           →  {}         (empty clause)
    """
    # Work with frozensets for hashability
    clause_set = {frozenset(c) for c in clauses}

    while True:
        new_clauses = set()
        clause_list = list(clause_set)

        for i in range(len(clause_list)):
            for j in range(i + 1, len(clause_list)):
                resolvents = _resolve_pair(clause_list[i], clause_list[j])

                for resolvent in resolvents:
                    if len(resolvent) == 0:
                        return True      # empty clause → contradiction

                    if resolvent not in clause_set:
                        new_clauses.add(resolvent)

        if not new_clauses:
            return False     # fixpoint — no contradiction

        clause_set |= new_clauses


def _resolve_pair(c1, c2):
    """
    Try to resolve two clauses on every complementary literal pair.
    Returns list of resolvents.

    Complementary pairs:
      P  and ("NOT", P)
      ("NOT", P) and P
    """
    resolvents = []

    for lit in c1:
        complement = _negate(lit)
        if complement in c2:
            # Resolve on this literal
            resolvent = (c1 - {lit}) | (c2 - {complement})
            resolvents.append(frozenset(resolvent))

    return resolvents


def _negate(literal):
    """
    Negate a literal:
      P          → ("NOT", P)
      ("NOT", P) → P
    """
    if isinstance(literal, tuple) and literal[0] == "NOT":
        return literal[1]
    return ("NOT", literal)

# ═════════════════════════════════════════════════════════════════════
# Stats
# ═════════════════════════════════════════════════════════════════════

def _make_stats(start_time, peak_bytes):
    return {
        'time_sec':    round(time.time() - start_time, 6),
        'peak_mem_kb': round(peak_bytes / 1024, 2),
    }