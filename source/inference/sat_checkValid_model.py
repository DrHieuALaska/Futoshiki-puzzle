# def check_solution(puzzle, clauses):
#     """
#     Validates a completed puzzle solution against grounded CNF clauses.
#     Returns True if the solution satisfies all clauses, False otherwise.
#     """
#     assignment = puzzle_to_assignment(puzzle)
#     return check_cnf(clauses, assignment)

# def check_cnf(clauses, assignment):
#     """
#     Validates a solution against grounded CNF clauses.
#     Returns True if all clauses are satisfied, False otherwise.
#     """
#     for clause in clauses:
#         # A clause is satisfied if at least one literal is True
#         if not any(_evaluate_literal(lit, assignment) for lit in clause):
#             # Useful for debugging: print(f"Failed clause: {clause}")
#             return False
#     return True

# def _evaluate_literal(literal, assignment):
#     """
#     Evaluates a single literal (either a positive atom or a NOT tuple).
#     """
#     # Case 1: Negated literal (e.g., ("NOT", ("Val", 0, 0, 1)))
#     if isinstance(literal, tuple) and literal[0] == "NOT": # eg: ("NOT", ("Val", 0, 0, 1))
#         atom = literal[1]
#         # In a valid model, if the atom is not present, we assume it is False,
#         # so NOT False = True.
#         return not assignment.get(atom, False)

#     # Case 2: Positive literal (e.g., ("Val", 0, 0, 1))
#     return assignment.get(literal, False)

# def puzzle_to_assignment(puzzle):
#     """
#     Converts a completed puzzle grid into a full SAT truth assignment.
#     This maps every possible Val(i, j, v) to True or False.
#     """
#     assignment = {}
#     N = puzzle.N

#     for i in range(N):
#         for j in range(N):
#             actual_val = puzzle.grid[i][j]
            
#             # Ground every possible value for this cell
#             for v in range(1, N + 1):
#                 atom = ("Val", i, j, v)
#                 if actual_val == v:
#                     assignment[atom] = True
#                 else:
#                     assignment[atom] = False
                    
#     return assignment


# -------------------------
# SAT Validator for Futoshiki
# -------------------------
from FOL.kb import KnowledgeBase

def validate_solution(kb: KnowledgeBase, solution_grid: list[list[int]]) -> tuple[bool, list]:
    """
    Check if solution_grid satisfies all CNF clauses in the KnowledgeBase.
    
    Args:
        kb:              KnowledgeBase already built from puzzle
        solution_grid:   2D list of ints (the proposed solution, no zeros)
    
    Returns:
        (is_valid, violations)  where violations is a list of unsatisfied clauses
    """
    # Build truth assignment from solution grid
    true_facts = _build_truth_assignment(kb, solution_grid)

    # Evaluate every clause
    violations = [
        clause for clause in kb.get_clauses()
        if not _eval_clause(clause, true_facts)
    ]

    return len(violations) == 0, violations


def _build_truth_assignment(kb: KnowledgeBase, solution_grid: list[list[int]]) -> set:
    """
    Construct the set of ground facts that are TRUE under this solution.
    Starts from KB facts (Given, LessH, GreaterH, etc.) and adds Val facts
    from the solution grid.
    """
    true_facts = set(kb.get_facts())  # already has Given + inequality facts

    N = len(solution_grid)
    for i in range(N):
        for j in range(N):
            v = solution_grid[i][j]
            if v != 0:
                true_facts.add(("Val", i, j, v))

    return true_facts


def _eval_clause(clause: tuple, true_facts: set) -> bool:
    """
    A clause (disjunction of literals) is satisfied if at least one literal is true.
    
    Literal forms:
        ("NOT", predicate)  →  true iff predicate NOT in true_facts
        predicate tuple     →  true iff predicate IN true_facts
    """
    for literal in clause:
        # At least one literal must be satisfied for the clause to hold
        if isinstance(literal, tuple) and literal[0] == "NOT":
            if literal[1] not in true_facts:
                return True         # negative literal satisfied
        else:
            if literal in true_facts:
                return True         # positive literal satisfied
    return False