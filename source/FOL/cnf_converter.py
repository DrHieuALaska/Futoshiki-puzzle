def _rule_to_clause(rule):
    """
    Convert a grounded implication to a CNF clause.

    P1 ∧ P2 → Q   becomes   ¬P1 ∨ ¬P2 ∨ Q
    P1 ∧ P2 → FALSE  becomes  ¬P1 ∨ ¬P2
    """
    premises   = rule["premises"]
    conclusion = rule["conclusion"]

    # Negate all premises
    clause = tuple(("NOT", p) for p in premises)

    # Add conclusion (unless FALSE — then clause is just negated premises)
    if conclusion != ("FALSE",):
        clause += (conclusion,)

    return clause