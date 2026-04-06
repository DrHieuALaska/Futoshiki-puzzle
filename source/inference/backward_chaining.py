# ─────────────────────────────────────────────────────────────────────
# SLD Resolution search
# ─────────────────────────────────────────────────────────────────────

def _sld_search(puzzle, N, facts, rules, assignment):
    """
    Recursive SLD resolution.

    At each step:
      1. Find the next unassigned cell
      2. For each candidate value v:
           - QUERY: is Val(i, j, v) consistent with current KB?
           - Prove consistency by attempting to derive FALSE
           - If FALSE not derivable -> safe -> assign and recurse
    """
    cell = _next_unassigned(N, assignment)
    if cell is None:
        return assignment  

    i, j = cell

    for v in range(1, N + 1):
        # Build candidate fact base with this tentative assignment
        candidate_facts = facts | {("Val", i, j, v)}

        # QUERY: backward chain to check if FALSE is derivable
        # If NOT derivable -> v is consistent
        if not _derive_false(rules, candidate_facts):
            new_assignment = dict(assignment)
            new_assignment[(i, j)] = v

            result = _sld_search(
                puzzle, N,
                candidate_facts,
                rules,
                new_assignment
            )
            if result is not None:
                return result

    return None 


# ─────────────────────────────────────────────────────────────────────
# Core: attempt to derive FALSE via SLD resolution
# ─────────────────────────────────────────────────────────────────────

def _derive_false(rules, facts):
    """
    Try to derive FALSE from the current fact base using the rule set.

    For each rule concluding FALSE:
      - Try to unify all premises against known facts
      - If a complete consistent binding exists -> FALSE derived -> True

    Returns:
        True  if a contradiction is found
        False if no rule fires
    """
    for rule in rules:
        name       = rule["name"]
        premises   = rule["premises"]
        condition  = rule.get("condition", lambda b: True)
        conclusion = rule["conclusion"]

        if conclusion != ("FALSE",):
            continue  

        # Try to find a binding that satisfies all premises
        for binding in _unify_all(premises, facts, {}):
            if condition(binding):
                return True  

    return False 


# ─────────────────────────────────────────────────────────────────────
# Unification engine
# ─────────────────────────────────────────────────────────────────────

def _unify_all(premises, facts, bindings):
    """
    Recursively unify a list of premise patterns against the fact base.
    Yields each complete consistent binding dict.

    This is the core of SLD resolution:
      - Take the first premise
      - Try to unify it with every fact
      - Recurse on the remaining premises with updated bindings
    """
    if not premises:
        yield bindings
        return

    first, *rest = premises

    # Apply current bindings to the pattern before matching
    pattern = _apply_bindings(first, bindings)

    for fact in facts:
        result = _unify_one(pattern, fact, bindings)
        if result is not None:
            yield from _unify_all(rest, facts, result)


def _unify_one(pattern, fact, bindings):
    """
    Try to unify a single pattern tuple against a ground fact.

    Rules:
      - "?x" is a variable -> bind to corresponding fact element
      - anything else      -> must match exactly

    Returns updated bindings dict, or None if unification fails.
    """
    if len(pattern) != len(fact):
        return None

    b = dict(bindings)

    for p, f in zip(pattern, fact):
        if isinstance(p, str) and p.startswith("?"):
            if p in b:
                if b[p] != f:
                    return None
            else:
                b[p] = f         
        else:
            if p != f:
                return None     

    return b


def _apply_bindings(pattern, bindings):
    """
    Substitute known variable bindings into a pattern tuple.

    Example:
        pattern  = ("Val", "?i", "?j", "?v1")
        bindings = {"?i": 0, "?j": 0}
        -> ("Val", 0, 0, "?v1")   ← ?v1 still unbound
    """
    return tuple(
        bindings.get(p, p) if (isinstance(p, str) and p.startswith("?")) else p
        for p in pattern
    )


# ─────────────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────────────

def _next_unassigned(N, assignment):
    """Return the first unassigned cell in row-major order."""
    for i in range(N):
        for j in range(N):
            if (i, j) not in assignment:
                return (i, j)
    return None