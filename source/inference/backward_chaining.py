from FOL.fol_builder import build_fol_symbolic_rules

# ─────────────────────────────────────────────────────────────────────
# SLD Resolution search
# ─────────────────────────────────────────────────────────────────────

def _sld_search(N, facts, facts_index, rules, assignment, domains):
    """
    Recursive SLD resolution with domain-based pruning.
 
    At each step:
      1. MRV: pick cell with fewest consistent values
      2. For each candidate value v:
           - Add Val(i,j,v) to facts tentatively
           - Update domains of remaining cells incrementally
           - If any domain becomes empty -> dead end, skip
           - Else recurse
    """
    if not domains:
        return assignment
 
    # MRV: pick cell with smallest domain
    (i, j) = min(domains, key=lambda c: len(domains[c]))
    candidates = domains[(i, j)]
 
    if not candidates:
        return None  # dead end
 
    for v in candidates:
        new_fact  = ("Val", i, j, v)
        new_facts = facts | {new_fact}
        new_fi    = _extend_index(facts_index, new_fact)
 
        # Incrementally update domains — detect conflict early
        new_domains, conflict = _update_domains(
            domains, i, j, v, new_facts, new_fi, rules
        )
 
        if conflict:
            continue
 
        new_assignment = {**assignment, (i, j): v}
        result = _sld_search(N, new_facts, new_fi, rules, new_assignment, new_domains)
        if result is not None:
            return result
 
    return None

# ─────────────────────────────────────────────────────────────────────
# Domain management
# ─────────────────────────────────────────────────────────────────────
 
def _compute_domain(i, j, N, facts, facts_index, rules):
    """
    Compute consistent values for cell (i,j).
    v is consistent if adding Val(i,j,v) does NOT derive FALSE.
    """
    domain = []
    for v in range(1, N + 1):
        new_fact = ("Val", i, j, v)
        new_fi   = _extend_index(facts_index, new_fact)
        if not _derive_false(rules, facts | {new_fact}, new_fi, new_fact):
            domain.append(v)
    return domain
 
 
def _update_domains(domains, assigned_i, assigned_j, assigned_v,
                    new_facts, new_fi, rules):
    """
    After assigning Val(assigned_i, assigned_j, assigned_v),
    filter each remaining cell's domain using incremental check.
 
    Returns (new_domains, conflict).
    conflict = True if any cell's domain wiped out.
    """
    new_fact    = ("Val", assigned_i, assigned_j, assigned_v)
    new_domains = {}
 
    for (ci, cj), old_domain in domains.items():
        if (ci, cj) == (assigned_i, assigned_j):
            continue
 
        filtered = []
        for cv in old_domain:
            cand_fact  = ("Val", ci, cj, cv)
            cand_facts = new_facts | {cand_fact}
            cand_fi    = _extend_index(new_fi, cand_fact)

            # Check contradiction from new_fact (new assignment)
            if _derive_false(rules, cand_facts, cand_fi, new_fact):
                continue
            # Check contradiction from cand_fact (testing)
            if _derive_false(rules, cand_facts, cand_fi, cand_fact):
                continue

            filtered.append(cv)
 
        if not filtered:
            return None, True  # conflict
 
        new_domains[(ci, cj)] = filtered
 
    return new_domains, False

# ─────────────────────────────────────────────────────────────────────
# Core: attempt to derive FALSE via SLD resolution
# ─────────────────────────────────────────────────────────────────────

def _derive_false(rules, facts, facts_index, trigger_fact):
    """
    Only check rules whose premises contain trigger_fact's predicate.
    Avoids re-checking rules that cannot possibly fire from the new fact.
    """
    trigger_pred = trigger_fact[0]
 
    for rule in rules:
        if rule["conclusion"] != ("FALSE",):
            continue
        premises = rule["premises"]
        if not any(p[0] == trigger_pred for p in premises):
            continue
        condition = rule.get("condition", lambda b: True)
        for binding in _unify_all(premises, facts, {}, facts_index):
            if condition(binding):
                return True
 
    return False

# ─────────────────────────────────────────────────────────────────────
# Unification engine
# ─────────────────────────────────────────────────────────────────────

def _unify_all(premises, facts, bindings, facts_index=None):
    """
    Recursively unify premises against facts.
    Uses facts_index to look up only facts with matching predicate.
    Yields each complete consistent binding.
    """
    if not premises:
        yield bindings
        return
 
    first, *rest = premises
    pattern   = _apply_bindings(first, bindings)
    predicate = pattern[0]
    candidates = facts_index.get(predicate, []) if facts_index else facts
 
    for fact in candidates:
        result = _unify_one(pattern, fact, bindings)
        if result is not None:
            yield from _unify_all(rest, facts, result, facts_index)
 
 
def _unify_one(pattern, fact, bindings):
    """Unify one pattern against one ground fact. Returns bindings or None."""
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
    """Substitute known bindings into a pattern. Unbound vars stay as-is."""
    return tuple(
        bindings.get(p, p) if (isinstance(p, str) and p.startswith("?")) else p
        for p in pattern
    )


# ─────────────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────────────

def _build_index(facts):
    """Build predicate -> [facts] index from scratch."""
    index = {}
    for fact in facts:
        index.setdefault(fact[0], []).append(fact)
    return index
 
 
def _extend_index(existing_index, new_fact):
    """
    Add one fact to an existing index without rebuilding from scratch.
    Returns a new index (does not mutate existing_index).
    """
    key = new_fact[0]
    new_index = dict(existing_index)
    new_index[key] = existing_index.get(key, []) + [new_fact]
    return new_index