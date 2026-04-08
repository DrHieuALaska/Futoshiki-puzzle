from FOL.cnf_converter import _rule_to_clause
def ground_to_clauses(facts, rules, N):
    clauses = []

    # Facts → unit clauses
    for fact in facts:
        clauses.append((fact,)) # wrap in tuple to make it a clause
    
    grounded_facts, grounded_rules = ground_kb(facts, rules, N)
    for rule in grounded_rules:
        clause = _rule_to_clause(rule)
        if clause:
            clauses.append(clause)

    return clauses

def ground_kb(facts, rules, N):
    """
    Ground symbolic FOL rules over concrete domain {1..N}.
    
    Replaces all ?variable patterns with concrete values by
    iterating over all possible combinations of {0..N-1} for
    index variables and {1..N} for value variables.
    
    This is what the teacher means by:
    "Instantiate FOL axioms over the concrete index domain {1..N}"
    """
    grounded_facts = list(facts)
    grounded_rules = []

    # Domain for index variables (rows, cols): 0..N-1
    # Domain for value variables: 1..N
    index_domain = list(range(N))
    value_domain = list(range(1, N + 1))

    for rule in rules:
        name       = rule["name"]
        premises   = rule["premises"]
        condition  = rule.get("condition", lambda b: True)
        conclusion = rule["conclusion"]

        # Identify all unique variables in this rule
        variables = _collect_variables(premises, conclusion)

        # Classify each variable as index or value
        var_domains = _assign_domains(variables, index_domain, value_domain)

        # Generate all combinations — cartesian product over variable domains
        for binding in _all_bindings(var_domains):
            # Check side condition with this binding
            if not condition(binding):
                continue

            # Instantiate premises
            ground_premises = [
                _instantiate(p, binding) for p in premises
            ]

            # Instantiate conclusion
            ground_conclusion = _instantiate(conclusion, binding)

            grounded_rules.append({
                "name":       name,
                "premises":   ground_premises,
                "conclusion": ground_conclusion
            })

    return grounded_facts, grounded_rules


# ─────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────

def _collect_variables(premises, conclusion):
    variables = set()
    all_preds = list(premises)
    if conclusion != ("FALSE",):
        all_preds.append(conclusion)          # don't iterate over FALSE

    for pred in all_preds:
        for arg in pred:
            if isinstance(arg, str) and arg.startswith("?"):
                variables.add(arg)
    return variables


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