def negate_literal(lit):
    if lit[0] == "NOT":
        return lit[1]
    else:
        return ("NOT", lit)


def resolve(ci, cj):
    """
    Try to resolve two clauses
    """
    resolvents = []

    for li in ci:
        for lj in cj:
            if li == negate_literal(lj):
                # Remove complementary literals
                new_clause = set(ci + cj)
                new_clause.discard(li)
                new_clause.discard(lj)

                resolvents.append(list(new_clause))

    return resolvents


def resolution(clauses):
    """
    Resolution algorithm
    Return True if contradiction found (empty clause)
    """

    clauses = [set(c) for c in clauses]

    new = set()

    while True:
        n = len(clauses)

        pairs = []
        for i in range(n):
            for j in range(i + 1, n):
                pairs.append((clauses[i], clauses[j]))

        for (ci, cj) in pairs:
            resolvents = resolve(list(ci), list(cj))

            for r in resolvents:
                if len(r) == 0:
                    return True  # contradiction found

                new.add(tuple(sorted(r)))

        if new.issubset(set(map(tuple, clauses))):
            return False  # no new clauses

        for c in new:
            clauses.append(set(c))