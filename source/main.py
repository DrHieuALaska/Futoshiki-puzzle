from input_output.parse_input import parse_input
from input_output.output_writer import write_output

from search.back_tracking import solve_backtracking
from search.brute_force import brute_force
from search.hybrid_backtracking_with_fc import solve_hybrid_backtracking_with_fc
from search.astar import solve_astar

from FOL.kb import KnowledgeBase

import os

# -------------------------
# Configuration
# -------------------------
TEST_CASES = [
    # ("01", "Inputs/input-01.txt", "3x3"),
    # ("02", "Inputs/input-02.txt", "3x3"),
    # ("03", "Inputs/input-03.txt", "5x5"),
    # ("04", "Inputs/input-04.txt", "5x5"),
    # ("05", "Inputs/input-05.txt", "6x6"),
    # ("06", "Inputs/input-06.txt", "6x6"),
    # ("07", "Inputs/input-07.txt", "6x6"),
    # ("08", "Inputs/input-08.txt", "6x6"),
    ("09", "Inputs/input-09.txt", "9x9"),
    ("10", "Inputs/input-10.txt", "9x9"),
    # ("11", "Inputs/input-11.txt", "9x9"),
    # ("12", "Inputs/input-12.txt", "9x9"),
]

OUTPUT_DIR = "Outputs"
HEURISTIC  = "remaining_unassigned_cells"


def run_one(tc_id: str, input_file: str, tc_size: str):
    output_file = os.path.join(OUTPUT_DIR, f"output-{tc_id}.txt")

    print("=" * 60)
    print(f"TEST CASE : {tc_id}  ({tc_size})")
    print(f"Input     : {input_file}")
    print(f"Output    : {output_file}")
    print("=" * 60)

    # ── 1. Parse ──────────────────────────────────────────────
    puzzle = parse_input(input_file)
    print("=== INPUT PUZZLE ===")
    print(puzzle)
    print()

    KB = KnowledgeBase(puzzle)  # also builds FOL + CNF, but we don't use it for solving in this implementation

    # ── 2. Solve ──────────────────────────────────────────────
    solution, astar_stats = solve_astar(puzzle.copy(), KB, heuristic="ac3")

    if solution is None:
        print("No solution found.\n")
        return

    print("=== SOLUTION ===")
    print(solution)
    print(f"Expansions : {astar_stats['expansions']}")
    print(f"Generated  : {astar_stats['generated']}")
    print(f"Time (s)   : {astar_stats['time_sec']:.6f}")
    print(f"Memory (KB): {astar_stats['peak_mem_kb']:.2f}")
    print()


    # ── 5. Write output ───────────────────────────────────────
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    write_output(solution, output_file)
    print(f"Output written to {output_file}\n")


def main():
    for tc_id, tc_path, tc_size in TEST_CASES:
        try:
            run_one(tc_id, tc_path, tc_size)
        except Exception as e:
            print(f"[ERROR] {tc_id} ({tc_path}) failed: {e}\n")


if __name__ == "__main__":
    main()