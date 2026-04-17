from FOL.cnf_converter import _rule_to_clause

def ground_to_clauses(facts, rules, N):
    clauses = []

    # Facts → unit clauses (already ground)
    for fact in facts:
        clauses.append((fact,))

    index_domain = list(range(N))
    value_domain = list(range(1, N + 1))

    for rule in rules:
        # ── Step 1: CNF conversion on the SYMBOLIC rule (done once per rule)
        symbolic_clause = _rule_to_clause(rule)
        if not symbolic_clause:
            continue

        condition = rule.get("condition", lambda b: True)

        # ── Step 2: collect variables from the symbolic clause, not the rule dict
        variables = _collect_vars_from_clause(symbolic_clause)
        var_domains = _assign_domains(variables, index_domain, value_domain)

        # ── Step 3: ground the symbolic clause
        for binding in _all_bindings(var_domains):
            if not condition(binding):
                continue

            ground_clause = tuple(
                _instantiate_literal(lit, binding)
                for lit in symbolic_clause
            )
            clauses.append(ground_clause)

    return clauses


# ── Helpers ───────────────────────────────────────────────────────────────────

def _collect_vars_from_clause(clause):
    """Collect all ?variables that appear inside a symbolic CNF clause."""
    variables = set()
    for literal in clause:
        pred = literal[1] if literal[0] == "NOT" else literal
        for arg in pred[1:]:           # skip the predicate name at index 0
            if isinstance(arg, str) and arg.startswith("?"):
                variables.add(arg)
    return variables


def _instantiate_literal(literal, binding):
    """Ground a single CNF literal — handles both positive and negated forms."""
    if literal[0] == "NOT":
        return ("NOT", _instantiate(literal[1], binding))
    return _instantiate(literal, binding)

def _assign_domains(variables, index_domain, value_domain):
    """
    Classify variables by naming convention:
      ?i, ?i1, ?i2  → row index domain
      ?j, ?j1, ?j2  → col index domain
      ?v, ?v1, ?v2  → value domain
    """
    var_domains = {}
    for var in variables:
        # Value variables
        if var.startswith("?v"):
            var_domains[var] = value_domain
        # Index variables (rows and cols both use same index domain)
        else:
            var_domains[var] = index_domain
    return var_domains


def _all_bindings(var_domains):
    """Generate all combinations of variable assignments (cartesian product)."""
    from itertools import product

    if not var_domains:
        yield {}
        return

    variables = list(var_domains.keys())
    domains   = [var_domains[v] for v in variables]

    for combo in product(*domains):
        yield dict(zip(variables, combo))


def _instantiate(predicate, binding):
    """Replace all ?variables in a predicate tuple with bound values."""
    return tuple(
        binding.get(arg, arg) if (isinstance(arg, str) and arg.startswith("?")) else arg
        for arg in predicate
    )