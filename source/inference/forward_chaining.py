from model.constraints import is_valid


def forward_chaining_solve(puzzle):
    """
    Solve using constraint propagation (FOL-style)
    """

    # Step 1: Initialize domains
    domains = {
        (i, j): set(range(1, puzzle.N + 1))
        for i in range(puzzle.N)
        for j in range(puzzle.N)
    }

    # Apply given values
    for i in range(puzzle.N):
        for j in range(puzzle.N):
            val = puzzle.grid[i][j]
            if val != 0:
                domains[(i, j)] = {val}

    # Step 2: Forward propagate constraints
    if not forward_propagate(puzzle, domains):
        return None  # contradiction found

    # Step 3: Check if solved
    solution = puzzle.copy()

    for (i, j), domain in domains.items():
        if len(domain) == 1:
            solution.grid[i][j] = next(iter(domain))
        else:
            return None  # not fully solved

    return solution

def propagate_inequality(puzzle, domains, i, j):
    changed = False
    val_set = domains[(i, j)]

    # Only act if single value
    if len(val_set) != 1:
        return True, False

    val = next(iter(val_set))

    # Right neighbor
    if j < puzzle.N - 1:
        constraint = puzzle.h_constraints[i][j]
        neighbor = (i, j + 1)
        new_domain = domains[neighbor] # default: no change, avoid uninitialized new_domain if constraint == 0:

        if constraint == 1:  # <
            new_domain = {v for v in domains[neighbor] if v > val}

        elif constraint == -1:  # >
            new_domain = {v for v in domains[neighbor] if v < val}
        
        if new_domain != domains[neighbor]:
            domains[neighbor] = new_domain
            changed = True
            if len(new_domain) == 0: # contradiction
                return False
        

    # Left neighbor
    if j > 0:
        constraint = puzzle.h_constraints[i][j - 1]
        neighbor = (i, j - 1)
        new_domain = domains[neighbor] # default: no change

        if constraint == 1:  # left < current
            new_domain = {v for v in domains[neighbor] if v < val}

        elif constraint == -1:  # left > current
            new_domain = {v for v in domains[neighbor] if v > val}
        
        if new_domain != domains[neighbor]:
            domains[neighbor] = new_domain
            changed = True
            if len(new_domain) == 0: # contradiction
                return False

    # Down neighbor
    if i < puzzle.N - 1:
        constraint = puzzle.v_constraints[i][j]
        neighbor = (i + 1, j)
        new_domain = domains[neighbor] # default: no change

        if constraint == 1:  # <
            new_domain = {v for v in domains[neighbor] if v > val}

        elif constraint == -1:  # >
            new_domain = {v for v in domains[neighbor] if v < val}

        if new_domain != domains[neighbor]:
            domains[neighbor] = new_domain
            changed = True
            if len(new_domain) == 0: # contradiction
                return False
    
    # Up neighbor
    if i > 0:
        constraint = puzzle.v_constraints[i - 1][j]
        neighbor = (i - 1, j)
        new_domain = domains[neighbor] # default: no change

        if constraint == 1:  # up < current
            new_domain = {v for v in domains[neighbor] if v < val}

        elif constraint == -1:  # up > current
            new_domain = {v for v in domains[neighbor] if v > val}
        
        if new_domain != domains[neighbor]:
            domains[neighbor] = new_domain
            changed = True
            if len(new_domain) == 0: # contradiction
                return False

    return True, changed

def forward_propagate(puzzle, domains):
    """
    Apply constraints repeatedly until no change
    Return False if contradiction found
    """
    changed = True

    while changed:
        changed = False

        for i in range(puzzle.N):
            for j in range(puzzle.N):
                if len(domains[(i, j)]) == 1:
                    val = next(iter(domains[(i, j)])) # single value assigned

                    # Row + Column elimination
                    for k in range(puzzle.N):
                        if k != j and val in domains[(i, k)]:
                            domains[(i, k)].discard(val)
                            if len(domains[(i, k)]) == 0: # contradiction
                                return False
                            changed = True

                        if k != i and val in domains[(k, j)]:
                            domains[(k, j)].discard(val)
                            if len(domains[(k, j)]) == 0: # contradiction
                                return False
                            changed = True

                    # Inequality constraints
                    no_contradiction, local_changed = propagate_inequality(puzzle, domains, i, j)
                    changed = changed or local_changed # if any change from inequality propagation
                    if not no_contradiction:
                        return False

    # Check contradiction
    for vals in domains.values():
        if len(vals) == 0:
            return False

    return True