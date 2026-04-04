def forward_chaining(puzzle, facts, domains):
    # ── propagate ─────────────────────────────────────────────
    changed = True
    N = puzzle.getN()

    while changed:
        changed = False

        # A2: cell assigned v → remove v from nothing (domain already fixed)
        # A3: Val(i,j1,v) assigned → remove v from all other cells in row
        changed |= _propagate_row(facts, domains, N)

        # A4: Val(i1,j,v) assigned → remove v from all other cells in col
        changed |= _propagate_col(facts, domains, N)

        # A5/A6: inequality constraints → restrict domains
        changed |= _propagate_inequalities(facts, domains, puzzle)

        # Derive new Val facts when domain collapses to 1
        changed |= _derive_val_facts(facts, domains)

        # Contradiction: any domain became empty
        if any(len(d) == 0 for d in domains.values()):
            return False, facts, domains

    return True, facts, domains


# ─────────────────────────────────────────────────────────────────────
# Propagation helpers
# ─────────────────────────────────────────────────────────────────────

def _propagate_row(facts, domains, N):
    """A3: if Val(i,j,v) is known, remove v from all other cells in row i."""
    changed = False
    for fact in list(facts):
        if fact[0] == "Val":
            _, i, j, v = fact
            for j2 in range(N):
                if j2 != j and v in domains[(i, j2)]:
                    domains[(i, j2)].discard(v)
                    changed = True
    return changed


def _propagate_col(facts, domains, N):
    """A4: if Val(i,j,v) is known, remove v from all other cells in col j."""
    changed = False
    for fact in list(facts):
        if fact[0] == "Val":
            _, i, j, v = fact
            for i2 in range(N):
                if i2 != i and v in domains[(i2, j)]:
                    domains[(i2, j)].discard(v)
                    changed = True
    return changed


def _propagate_inequalities(facts, domains, puzzle):
    """
    Inequality propagation:
      LessH(i,j)   → domain[i][j]   must be < some value in domain[i][j+1]
                   → domain[i][j+1] must be > some value in domain[i][j]
      GreaterH(i,j) → opposite
      Same for LessV / GreaterV
    """
    changed = False
    N = puzzle.getN()

    for fact in facts:
        tag = fact[0]

        if tag == "LessH":
            # grid[i][j] < grid[i][j+1]
            _, i, j = fact
            changed |= _apply_less(domains, (i, j), (i, j + 1))

        elif tag == "GreaterH":
            # grid[i][j] > grid[i][j+1]
            _, i, j = fact
            changed |= _apply_less(domains, (i, j + 1), (i, j))

        elif tag == "LessV":
            # grid[i][j] < grid[i+1][j]
            _, i, j = fact
            changed |= _apply_less(domains, (i, j), (i + 1, j))

        elif tag == "GreaterV":
            # grid[i][j] > grid[i+1][j]
            _, i, j = fact
            changed |= _apply_less(domains, (i + 1, j), (i, j))

    return changed


def _apply_less(domains, smaller_cell, larger_cell):
    """
    Enforce: value of smaller_cell < value of larger_cell.

    - Remove from smaller_cell any v >= max(larger_cell domain)
    - Remove from larger_cell any v <= min(smaller_cell domain)
    """
    changed = False
    d_small = domains[smaller_cell]
    d_large = domains[larger_cell]

    if not d_small or not d_large:
        return False

    max_large = max(d_large)
    min_small = min(d_small)

    # smaller_cell values must be < max_large
    new_small = {v for v in d_small if v < max_large}
    if new_small != d_small:
        domains[smaller_cell] = new_small
        changed = True

    # larger_cell values must be > min_small
    new_large = {v for v in d_large if v > min_small}
    if new_large != d_large:
        domains[larger_cell] = new_large
        changed = True

    return changed


def _derive_val_facts(facts, domains):
    """
    When a domain collapses to exactly 1 value → derive Val(i,j,v) fact.
    This is where forward chaining actually produces NEW positive facts.
    """
    changed = False
    for (i, j), domain in domains.items():
        if len(domain) == 1:
            v = next(iter(domain))
            val_fact = ("Val", i, j, v)
            if val_fact not in facts:
                facts.add(val_fact)
                changed = True
    return changed