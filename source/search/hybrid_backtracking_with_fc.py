from inference.forward_chaining import forward_chaining

def solve_hybrid_backtracking_with_fc(puzzle, kb):
    N = puzzle.getN()
    facts = set(kb.get_facts())

    # ── build initial domains ────────────────────────────────
    # Start with full domain {1..N} for every cell
    domains = {(i, j): set(range(1, N + 1))
               for i in range(N) for j in range(N)}

    # Fix domains for cells that already have a Val fact
    for fact in facts:
        if fact[0] == "Val":
            _, i, j, v = fact
            domains[(i, j)] = {v}

    return backtrack_with_fc(puzzle, facts, domains)


def backtrack_with_fc(puzzle, facts, domains):
    # 1. Deep Copy before mutating — never touch caller's state
    working_domains = copy_domains(domains)
    working_facts = set(facts)

    # 2. Forward propagation on working copies
    valid, working_facts, working_domains = forward_chaining(
        puzzle, working_facts, working_domains
    )

    if not valid:
        return None  # contradiction

    # 2. Check if solved
    if all(len(working_domains[cell]) == 1 for cell in working_domains):
        solution = puzzle.copy()
        for (i, j), vals in working_domains.items():
            solution.grid[i][j] = next(iter(vals)) # Assign the single value in domain to solution
        return solution

    # 3. Choose cell (MRV)
    cell = select_mrv(working_domains)
    i, j = cell

    # 4. Try values
    for val in list(working_domains[cell]):
        # deep copy domains
        new_domains = copy_domains(working_domains)
        new_domains[(i, j)] = {val}
        candidate_facts = working_facts | {("Val", i, j, val)}

        result = backtrack_with_fc(puzzle, candidate_facts, new_domains)
        if result:
            return result 

    return None

def select_mrv(domains):
    return min(
        (cell for cell in domains if len(domains[cell]) > 1),
        key=lambda c: len(domains[c])
    )

def copy_domains(domains):
    return {k: set(v) for k, v in domains.items()}