def check_cnf(clauses, assignment):
    """
    clauses: list of clauses
    assignment: truth assignment

    Return True if all clauses satisfied (check if solution is valid)
    """
    for clause in clauses:
        if not evaluate_clause(clause, assignment):
            return False
    return True

def evaluate_clause(clause, assignment):
    """
    clause: list of literals (OR)
    """
    return any(evaluate_literal(lit, assignment) for lit in clause)

def evaluate_literal(literal, assignment):
    """
    literal: ("Val", i, j, v) OR ("NOT", predicate)
    assignment: dict mapping predicate → True/False
    """

    # Negated literal
    if literal[0] == "NOT":
        pred = literal[1]
        return not assignment.get(pred, False)

    # Positive literal
    return assignment.get(literal, False) 


def puzzle_to_assignment(puzzle):
    assignment = {}

    for i in range(puzzle.N):
        for j in range(puzzle.N):
            val = puzzle.grid[i][j]

            if val != 0:
                assignment[("Val", i, j, val)] = True

                # All other values = False
                for v in range(1, puzzle.N + 1):
                    if v != val:
                        assignment[("Val", i, j, v)] = False

    return assignment