# -------------------------
# Predicate Representation
# -------------------------

def Val(i, j, v):    return ("Val", i, j, v)
def Given(i, j, v):  return ("Given", i, j, v)
def LessH(i, j):     return ("LessH", i, j)
def GreaterH(i, j):  return ("GreaterH", i, j)
def LessV(i, j):     return ("LessV", i, j)
def GreaterV(i, j):  return ("GreaterV", i, j)

def implies(premises, conclusion):
    return ("IMPLIES", premises, conclusion)


# -------------------------
# Build FOL Knowledge Base
# -------------------------

def build_fol_facts(puzzle):
    N = puzzle.N
    facts = []

    # -------------------------
    # 1. Given clues → facts
    # -------------------------
    for i in range(N):
        for j in range(N):
            val = puzzle.grid[i][j]
            if val != 0:
                facts.append(Given(i, j, val))
                facts.append(Val(i, j, val))

    # -------------------------
    # 2. Inequality constraints → facts
    #    (only emit facts where constraint actually exists)
    # -------------------------
    for i in range(N):
        for j in range(N - 1):
            c = puzzle.h_constraints[i][j]
            if c == 1:
                facts.append(LessH(i, j))
            elif c == -1:
                facts.append(GreaterH(i, j))

    for i in range(N - 1):
        for j in range(N):
            c = puzzle.v_constraints[i][j]
            if c == 1:
                facts.append(LessV(i, j))
            elif c == -1:
                facts.append(GreaterV(i, j))

    return facts

# ONE rule replaces hundreds of ground instances
def build_fol_rules(puzzle):
    N = puzzle.N
    rules = []  # rules stay symbolic with variables

    # RULES: use variable placeholders — grounding happens at inference time
    rules = [
        # A2: at most one value per cell
        # ∀ i,j,v1,v2 (v1≠v2): Val(i,j,v1) ∧ Val(i,j,v2) → FALSE
        {
            "name": "cell_uniqueness",
            "premises": [Val("?i", "?j", "?v1"), Val("?i", "?j", "?v2")],
            "condition": lambda b: b["?v1"] != b["?v2"],
            "conclusion": ("FALSE",) 
        },
        # A3: row uniqueness
        # ∀ i,j1,j2,v (j1≠j2): Val(i,j1,v) ∧ Val(i,j2,v) → FALSE
        {
            "name": "row_uniqueness",
            "premises": [Val("?i", "?j1", "?v"), Val("?i", "?j2", "?v")],
            "condition": lambda b: b["?j1"] != b["?j2"],
            "conclusion": ("FALSE",)
        },
        # A4: column uniqueness
        {
            "name": "col_uniqueness",
            "premises": [Val("?i1", "?j", "?v"), Val("?i2", "?j", "?v")],
            "condition": lambda b: b["?i1"] != b["?i2"],
            "conclusion": ("FALSE",)
        },
        # A5: horizontal inequality  grid[i][j] < grid[i][j+1]
        # ∀ i,j,v1,v2: LessH(i,j) ∧ Val(i,j,v1) ∧ Val(i,j+1,v2) ∧ v1≥v2 → FALSE
        {
            "name": "less_horizontal",
            "premises": [LessH("?i", "?j"), Val("?i", "?j", "?v1"), Val("?i", "?j1", "?v2")],
            "condition": lambda b: b["?j1"] == b["?j"] + 1 and b["?v1"] >= b["?v2"],
            "conclusion": ("FALSE",)
        },
        {
            "name": "greater_horizontal",
            "premises": [GreaterH("?i", "?j"), Val("?i", "?j", "?v1"), Val("?i", "?j1", "?v2")],
            "condition": lambda b: b["?j1"] == b["?j"] + 1 and b["?v1"] <= b["?v2"],
            "conclusion": ("FALSE",)
        },

        # A6: vertical inequality
        {
            "name": "less_vertical",
            "premises": [LessV("?i", "?j"), Val("?i", "?j", "?v1"), Val("?i1", "?j", "?v2")],
            "condition": lambda b: b["?i1"] == b["?i"] + 1 and b["?v1"] >= b["?v2"],
            "conclusion": ("FALSE",)
        },
        {
            "name": "greater_vertical",
            "premises": [GreaterV("?i", "?j"), Val("?i", "?j", "?v1"), Val("?i1", "?j", "?v2")],
            "condition": lambda b: b["?i1"] == b["?i"] + 1 and b["?v1"] <= b["?v2"],
            "conclusion": ("FALSE",)
        },
    ]

    return rules