from inference.backward_chaining import _build_index, _compute_domain, _sld_search

"""
Backward Chaining (SLD Resolution) solver for Futoshiki.

Strategy:
  - GOAL: prove Val(i, j, v) for every empty cell
  - To prove Val(i, j, v) is safe:
      Tentatively add it, then try to derive FALSE via rules
      If FALSE is NOT derivable => v is consistent => accept it
  - Uses depth-first SLD resolution (Prolog-style)
"""


# ─────────────────────────────────────────────────────────────────────
# Public entry point
# ─────────────────────────────────────────────────────────────────────

def backward_chaining_solve(puzzle, kb):
    """
    Entry point. Extracts facts/rules and starts recursive SLD search.
    """
    N = puzzle.getN()
    rules = kb.get_symbolic_rules()
    facts = set(kb.get_facts())     
    facts_index = _build_index(facts)

    assignment = {}
    for fact in facts:
        if fact[0] == "Val":
            _, i, j, v = fact
            assignment[(i, j)] = v

    domains = {}
    for i in range(N):
        for j in range(N):
            if (i, j) not in assignment:
                domains[(i, j)] = _compute_domain(i, j, N, facts, facts_index, rules)

    result = _sld_search(N, facts, facts_index, rules, assignment, domains)
    if result is None:
        return None

    solution = puzzle.copy()
    for (i, j), v in result.items():
        solution.grid[i][j] = v
    return solution
