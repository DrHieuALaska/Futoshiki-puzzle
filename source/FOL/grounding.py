def ground_kb(facts, rules):
    """Ground the knowledge base by replacing variables with all possible constants."""
    grounded_facts = list(facts)
    grounded_rules = list(rules)

    return grounded_facts, grounded_rules