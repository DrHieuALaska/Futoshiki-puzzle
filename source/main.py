from input_output.parse_input import parse_input
from input_output.output_writer import write_output

from search.back_tracking import solve_backtracking
from search.hybrid_backtracking_with_fc import solve_hybrid_backtracking_with_fc
from search.forward_chaining_solve import forward_chaining_solve

from FOL.kb import KnowledgeBase

from inference.resolution import resolution

from search.brute_force import brute_force
from input_output.output_writer import write_output


def main():
    # -------------------------
    # 1. Choose input file
    # -------------------------
    input_file = "Inputs/input-02.txt"
    output_file = "Outputs/output-02.txt"

    # -------------------------
    # 2. Parse input
    # -------------------------
    puzzle = parse_input(input_file)

    KB = KnowledgeBase(puzzle)

    # -------------------------
    # 3. Solve
    # -------------------------
    # solution = solve_backtracking(puzzle)
    solution = solve_hybrid_backtracking_with_fc(puzzle, KB)

    if solution is None:
        print("❌ No solution found")
        return

    print("✅ Solution found:")
    print(solution)
    print()

    # -------------------------
    # 6. Write output
    # -------------------------
    write_output(solution, output_file)
    print(f"📄 Output written to {output_file}")


if __name__ == "__main__":
    main()

