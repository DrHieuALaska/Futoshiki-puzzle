def forward_chaining(facts, rules, domains, history=None):
    """
    FOL Forward Chaining via Modus Ponens.

    For each unresolved cell (i,j) and each value v in domain(i,j):
        - Tentatively add Val(i,j,v) to facts
        - Check if any rule fires FALSE via unification
        - If yes → v violates a constraint → eliminate from domain
        - If domain collapses to 1 → derive Val(i,j,v) as new fact
        - If domain collapses to 0 → contradiction
    """
    if history is None:
        history = []
    facts   = set(facts)
    changed = True

    facts_index = _build_index(facts)
    is_complete = True
    is_valid    = True

    if _facts_have_contradiction(rules, facts, facts_index):
        is_valid = False
        is_complete = False
        return is_valid, is_complete, facts, domains

    while changed:
        changed = False

        # ── Modus Ponens elimination ───────────────────────────────────
        for (i, j) in list(domains.keys()):
            if len(domains[(i, j)]) <= 1:
                continue    # already fixed — skip

            to_remove = set()
            for v in list(domains[(i, j)]):

                # Tentatively add Val(i,j,v) and test for contradiction
                candidate      = ("Val", i, j, v)
                test_facts     = facts | {candidate}
                test_index     = _extend_index(facts_index, candidate)

                # Modus Ponens: does any rule fire → FALSE?
                if _any_rule_fires_false(rules, test_facts, test_index, candidate):
                    to_remove.add(v)

            if to_remove:
                for removed_val in sorted(to_remove):
                    history.append(('eliminate', i, j, removed_val))
                domains[(i, j)] -= to_remove
                changed = True

        # ── Domain collapse check ──────────────────────────────────────
        for (i, j), domain in domains.items():

            if len(domain) == 0:
                is_valid = False
                is_complete = False
                return is_valid, is_complete, facts, domains    # contradiction

            if len(domain) == 1:
                v        = next(iter(domain))
                val_fact = ("Val", i, j, v)
                if val_fact not in facts:
                    facts.add(val_fact)
                    facts_index = _extend_index(facts_index, val_fact)
                    if _any_rule_fires_false(rules, facts, facts_index, val_fact):
                        is_valid = False
                        is_complete = False
                        return is_valid, is_complete, facts, domains
                    history.append(('derive', i, j, v))
                    changed = True              # new fact → re-run rules

    if _facts_have_contradiction(rules, facts, facts_index):
        is_valid = False
        is_complete = False
        return is_valid, is_complete, facts, domains

    for (i, j), domain in domains.items():
        if len(domain) != 1:
            is_complete = False
            is_valid = True   # no contradictions found, but not fully solved
            return is_valid, is_complete, facts, domains

    return is_valid, is_complete, facts, domains

def _facts_have_contradiction(rules, facts, facts_index):
    for fact in facts:
        if _any_rule_fires_false(rules, facts, facts_index, fact):
            return True
    return False

def _any_rule_fires_false(rules, facts, facts_index, trigger):
    """
    Check if any rule concluding FALSE can be unified against facts,
    where at least one premise involves the trigger fact's predicate.

    This is the Modus Ponens check:
        premises all in facts → conclusion (FALSE) derived
    """
    trigger_pred = trigger[0]

    for rule in rules:
        if rule["conclusion"] != ("FALSE",):
            continue

        premises  = rule["premises"]
        condition = rule.get("condition", lambda b: True)

        # Optimization: skip rules that can't involve the trigger
        if not any(p[0] == trigger_pred for p in premises):
            continue

        for binding in _unify_all(premises, facts, {}, facts_index):
            if condition(binding):
                return True     # Modus Ponens fired → FALSE derived

    return False


# ─────────────────────────────────────────────────────────────────────
# Unification engine (unchanged)
# ─────────────────────────────────────────────────────────────────────

def _unify_all(premises, facts, bindings, facts_index=None):
    if not premises:
        yield bindings
        return

    first, *rest = premises
    pattern      = _apply_bindings(first, bindings)
    predicate    = pattern[0]
    candidates   = facts_index.get(predicate, list(facts)) if facts_index else facts

    for fact in candidates:
        result = _unify_one(pattern, fact, bindings)
        if result is not None:
            yield from _unify_all(rest, facts, result, facts_index)


def _unify_one(pattern, fact, bindings):
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
    return tuple(
        bindings.get(p, p) if (isinstance(p, str) and p.startswith("?")) else p
        for p in pattern
    )


def _build_index(facts):
    index = {}
    for fact in facts:
        index.setdefault(fact[0], []).append(fact)
    return index


def _extend_index(existing_index, new_fact):
    key       = new_fact[0]
    new_index = dict(existing_index)
    new_index[key] = existing_index.get(key, []) + [new_fact]
    return new_index
