def to_cnf_clause(rule):
    """
    Convert one rule into a CNF clause
    Input:
        ("IMPLIES", premises, conclusion)
    Output:
        clause: list of literals
    """

    _, premises, conclusion = rule

    clause = []

    # Negate all premises
    for p in premises:
        clause.append(negate(p))

    # Add conclusion (if not FALSE)
    if conclusion != ("FALSE",):
        clause.append(conclusion)

    return clause


def negate(predicate):
    """
    Represent negation as ("NOT", predicate)
    """
    return ("NOT", predicate)


def convert_kb_to_cnf(rules):
    """
    Convert all rules into CNF clauses
    """
    clauses = []

    for rule in rules:
        clause = to_cnf_clause(rule)
        clauses.append(clause)

    return clauses