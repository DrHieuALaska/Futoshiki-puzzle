from inference.forward_chaining import forward_chaining

def forward_chaining_solve(puzzle, kb):
    N = puzzle.getN()
    facts = set(kb.get_facts())

    # ── Step 1: build initial domains ────────────────────────────────
    # Start with full domain {1..N} for every cell
    domains = {(i, j): set(range(1, N + 1))
               for i in range(N) for j in range(N)}

    # Fix domains for cells that already have a Val fact
    for fact in facts:
        if fact[0] == "Val":
            _, i, j, v = fact
            domains[(i, j)] = {v}

    # Step 2: Forward chaining solve
    valid, _, _ = forward_chaining(puzzle, facts, domains)
    if not valid:
        return False, None, None   # contradiction in initial KB

    # Step 3: Check if solved
    solution = puzzle.copy()
    is_complete = True

    for (i, j), domain in domains.items():
        if len(domain) == 1:
            solution.grid[i][j] = next(iter(domain))
        else:
            is_complete = False    # FC couldn't determine this cell

    return is_complete, solution, domains  # caller decides what to do
    