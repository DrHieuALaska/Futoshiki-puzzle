# -------------------------
# Predicate Representation
# -------------------------

def Val(i, j, v):
    return ("Val", i, j, v)


def Given(i, j, v):
    return ("Given", i, j, v)


def LessH(i, j):
    return ("LessH", i, j)


def GreaterH(i, j):
    return ("GreaterH", i, j)


def LessV(i, j):
    return ("LessV", i, j)


def GreaterV(i, j):
    return ("GreaterV", i, j)


def Less(v1, v2):
    return ("Less", v1, v2)


# -------------------------
# Rule Representation
# -------------------------

def implies(premises, conclusion):
    """
    premises: list of predicates
    conclusion: single predicate
    """
    return ("IMPLIES", premises, conclusion)


# -------------------------
# Build FOL Knowledge Base
# -------------------------

def build_fol_kb(puzzle):
    """
    Return:
        facts: list of ground facts
        rules: list of implication rules
    """

    N = puzzle.N
    facts = []
    rules = []

    # -------------------------
    # 1. Given clues → facts
    # -------------------------
    for i in range(N):
        for j in range(N):
            val = puzzle.grid[i][j]
            if val != 0:
                facts.append(Given(i, j, val))
                facts.append(Val(i, j, val))  # enforce directly

    # -------------------------
    # 2. Inequality constraints → facts
    # -------------------------
    # Horizontal
    for i in range(N):
        for j in range(N - 1):
            c = puzzle.h_constraints[i][j]
            if c == 1:
                facts.append(LessH(i, j))
            elif c == -1:
                facts.append(GreaterH(i, j))

    # Vertical
    for i in range(N - 1):
        for j in range(N):
            c = puzzle.v_constraints[i][j]
            if c == 1:
                facts.append(LessV(i, j))
            elif c == -1:
                facts.append(GreaterV(i, j))

    # -------------------------
    # 3. Axioms (RULES)
    # -------------------------

    # A1: Every cell has at least one value
    # (We don't fully encode existential here — handled in search)

    # A2: At most one value
    for i in range(N):
        for j in range(N):
            for v1 in range(1, N + 1):
                for v2 in range(1, N + 1):
                    if v1 != v2:
                        rules.append(
                            implies(
                                [Val(i, j, v1), Val(i, j, v2)],
                                ("FALSE",)
                            )
                        )

    # A3: Row uniqueness
    for i in range(N):
        for j1 in range(N):
            for j2 in range(N):
                if j1 != j2:
                    for v in range(1, N + 1):
                        rules.append(
                            implies(
                                [Val(i, j1, v), Val(i, j2, v)],
                                ("FALSE",)
                            )
                        )

    # A4: Column uniqueness
    for j in range(N):
        for i1 in range(N):
            for i2 in range(N):
                if i1 != i2:
                    for v in range(1, N + 1):
                        rules.append(
                            implies(
                                [Val(i1, j, v), Val(i2, j, v)],
                                ("FALSE",)
                            )
                        )

    # A5: Horizontal inequality
    for i in range(N):
        for j in range(N - 1):
            for v1 in range(1, N + 1):
                for v2 in range(1, N + 1):
                    if v1 >= v2:
                        rules.append(
                            implies(
                                [LessH(i, j), Val(i, j, v1), Val(i, j + 1, v2)],
                                ("FALSE",)
                            )
                        )

                    if v1 <= v2:
                        rules.append(
                            implies(
                                [GreaterH(i, j), Val(i, j, v1), Val(i, j + 1, v2)],
                                ("FALSE",)
                            )
                        )

    # A6: Vertical inequality
    for i in range(N - 1):
        for j in range(N):
            for v1 in range(1, N + 1):
                for v2 in range(1, N + 1):
                    if v1 >= v2:
                        rules.append(
                            implies(
                                [LessV(i, j), Val(i, j, v1), Val(i + 1, j, v2)],
                                ("FALSE",)
                            )
                        )

                    if v1 <= v2:
                        rules.append(
                            implies(
                                [GreaterV(i, j), Val(i, j, v1), Val(i + 1, j, v2)],
                                ("FALSE",)
                            )
                        )

    return facts, rules