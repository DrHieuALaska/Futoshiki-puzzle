from input_output.parse_input import parse_input
from input_output.output_writer import write_output

from search.back_tracking import solve_backtracking
from search.brute_force import brute_force
from search.hybrid_backtracking_with_fc import solve_hybrid_backtracking_with_fc
from search.astar import solve_astar

from FOL.fol_builder import build_fol_kb
from FOL.cnf_converter import convert_kb_to_cnf
from inference.sat_solver import puzzle_to_assignment, check_cnf


def main():
    # -------------------------
    # 1. Choose input file
    # -------------------------
    input_file = "Inputs/input-05.txt"
    output_file = "Outputs/output-05.txt"

    # -------------------------
    # 2. Parse input
    # -------------------------
    puzzle = parse_input(input_file)

    print("=== INPUT PUZZLE ===")
    print(puzzle)
    print()

    # -------------------------
    # 3. Solve
    # -------------------------
    # A* heuristic options:
    #   - "ac3"
    #   - "remaining_unassigned_cells"
    #   - "inequality_chains"
    # solution = brute_force(puzzle.copy())
    # solution = solve_backtracking(puzzle.copy())
    # solution = solve_hybrid_backtracking_with_fc(puzzle.copy())
    solution, astar_stats = solve_astar(puzzle.copy(), heuristic="inequality_chains")

    if solution is None:
        print("No solution found")
        return

    print("Solution found:")
    print(solution)
    print(f"Expansions: {astar_stats['expansions']}")
    print(f"Generated: {astar_stats['generated']}")
    print(f"Time (s): {astar_stats['time_sec']:.6f}")
    print(f"Memory (KB): {astar_stats['peak_mem_kb']:.2f}")
    print()

    # -------------------------
    # 4. Build FOL + CNF
    # -------------------------
    print("Building FOL knowledge base...")
    facts, rules = build_fol_kb(puzzle)


    print(f"Facts: {len(facts)}")
    print(f"Rules: {len(rules)}")

    print("Converting to CNF...")
    clauses = convert_kb_to_cnf(rules)
    print(f"Clauses: {len(clauses)}")
    print()

    # -------------------------
    # 5. Validate solution using CNF
    # -------------------------
    print("Validating solution with CNF...")
    assignment = puzzle_to_assignment(solution)
    is_valid = check_cnf(clauses, assignment)

    if is_valid:
        print("CNF validation PASSED")
    else:
        print("CNF validation FAILED")
    print()

    # -------------------------
    # 6. Write output
    # -------------------------
    write_output(solution, output_file)
    print(f"Output written to {output_file}")


if __name__ == "__main__":
    main()
