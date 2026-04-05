# from input_output.parse_input import parse_input
# from input_output.output_writer import write_output

# from search.back_tracking import solve_backtracking
# from search.brute_force import brute_force
# from search.hybrid_backtracking_with_fc import solve_hybrid_backtracking_with_fc
# from search.astar import solve_astar
# from search.forward_chaining_solve import forward_chaining_solve


# from FOL.kb import KnowledgeBase

# import os

# # -------------------------
# # Configuration
# # -------------------------
# TEST_CASES = [
#     # ("01", "Inputs/input-01.txt", "3x3"),
#     # ("02", "Inputs/input-02.txt", "3x3"),
#     # ("03", "Inputs/input-03.txt", "5x5"),
#     # ("04", "Inputs/input-04.txt", "5x5"),
#     # ("05", "Inputs/input-05.txt", "6x6"),
#     # ("06", "Inputs/input-06.txt", "6x6"),
#     # ("07", "Inputs/input-07.txt", "6x6"),
#     # ("08", "Inputs/input-08.txt", "6x6"),
#     ("09", "Inputs/input-09.txt", "9x9"),
#     ("10", "Inputs/input-10.txt", "9x9"),
#     # ("11", "Inputs/input-11.txt", "9x9"),
#     # ("12", "Inputs/input-12.txt", "9x9"),
# ]

# OUTPUT_DIR = "Outputs"
# HEURISTIC  = "remaining_unassigned_cells"


# def run_one(tc_id: str, input_file: str, tc_size: str):
#     output_file = os.path.join(OUTPUT_DIR, f"output-{tc_id}.txt")

#     print("=" * 60)
#     print(f"TEST CASE : {tc_id}  ({tc_size})")
#     print(f"Input     : {input_file}")
#     print(f"Output    : {output_file}")
#     print("=" * 60)

#     # ── 1. Parse ──────────────────────────────────────────────
#     puzzle = parse_input(input_file)
#     print("=== INPUT PUZZLE ===")
#     print(puzzle)
#     print()

#     KB = KnowledgeBase(puzzle)  # also builds FOL + CNF, but we don't use it for solving in this implementation

#     # ── 2. Solve ──────────────────────────────────────────────
#     solution, astar_stats = solve_astar(puzzle, KB, heuristic="ac3")
#     # is_complete, solution, domains, fc_stats = forward_chaining_solve(puzzle.copy(), KB)
#     #solution, backtracking_stats = solve_backtracking(puzzle)
#     #solution, brute_force_stats = brute_force(puzzle)
#     #solution, hybrid_stats = solve_hybrid_backtracking_with_fc(puzzle, KB) 

#     if solution is None:
#         print("No solution found.\n")
#         return

#     print("=== SOLUTION ===")
#     print(solution)
#     print(f"Expansions : {astar_stats['expansions']}")
#     print(f"Generated  : {astar_stats['generated']}")
#     print(f"Time (s)   : {astar_stats['time_sec']:.6f}")
#     print(f"Memory (KB): {astar_stats['peak_mem_kb']:.2f}")
#     print()


#     # ── 5. Write output ───────────────────────────────────────
#     os.makedirs(OUTPUT_DIR, exist_ok=True)
#     write_output(solution, output_file)
#     print(f"Output written to {output_file}\n")


# def main():
#     for tc_id, tc_path, tc_size in TEST_CASES:
#         try:
#             run_one(tc_id, tc_path, tc_size)
#         except Exception as e:
#             print(f"[ERROR] {tc_id} ({tc_path}) failed: {e}\n")


# if __name__ == "__main__":
#     main()

import os

from input_output.parse_input import parse_input
from input_output.output_writer import write_output

from search.back_tracking import solve_backtracking
from search.brute_force import brute_force
from search.hybrid_backtracking_with_fc import solve_hybrid_backtracking_with_fc
from search.astar import solve_astar
from search.forward_chaining_solve import forward_chaining_solve

from FOL.kb import KnowledgeBase


# ============================================================
# USER CONFIG
# ============================================================

ALGORITHM = "astar"   # options: backtracking, astar, bruteforce, forward_chaining, hybrid
DIFFICULTY = "easy"   # easy, medium, hard
SIZE = "4x4"          # 4x4 → 9x9
TEST_IDS = ["01", "02", "03"]  # which files to run
HEURISTIC = "ac3"     # for A* only


INPUT_ROOT = "Inputs"
OUTPUT_ROOT = "Outputs"


# ============================================================
# SOLVER DISPATCH
# ============================================================

def run_solver(puzzle, kb):
    if ALGORITHM == "astar":
        return solve_astar(puzzle, kb, heuristic=HEURISTIC)

    elif ALGORITHM == "backtracking":
        solution, stats = solve_backtracking(puzzle)
        return solution, stats

    elif ALGORITHM == "bruteforce":
        solution, stats = brute_force(puzzle)
        return solution, stats

    elif ALGORITHM == "forward_chaining":
        is_complete, solution, domains, stats = forward_chaining_solve(puzzle, kb)
        return solution if is_complete else None, stats

    elif ALGORITHM == "hybrid":
        solution, stats = solve_hybrid_backtracking_with_fc(puzzle, kb)
        return solution, stats

    else:
        raise ValueError(f"Unknown algorithm: {ALGORITHM}")


# ============================================================
# CORE RUNNER
# ============================================================

def run_one(test_id):
    input_file = os.path.join(INPUT_ROOT, DIFFICULTY, SIZE, f"input-{test_id}.txt")
    output_file = os.path.join(OUTPUT_ROOT, DIFFICULTY, SIZE, f"output-{test_id}.txt")

    print("=" * 60)
    print(f"TEST CASE : {test_id} ({DIFFICULTY}/{SIZE})")
    print(f"Algorithm : {ALGORITHM}")
    print(f"Input     : {input_file}")
    print(f"Output    : {output_file}")
    print("=" * 60)

    # ── Parse ─────────────────────────────
    puzzle = parse_input(input_file)
    print("=== INPUT PUZZLE ===")
    print(puzzle)
    print()

    kb = KnowledgeBase(puzzle)

    # ── Solve ─────────────────────────────
    solution, stats = run_solver(puzzle, kb)

    if solution is None:
        print("❌ No solution found.\n")
        return

    # ── Print ─────────────────────────────
    print("=== SOLUTION ===")
    print(solution)

    if stats:
        if(ALGORITHM == "astar"):
            print(f"Expansions : {stats.get('expansions', '-')}")
            print(f"Generated  : {stats.get('generated', '-')}")
        print(f"Time (s)   : {stats.get('time_sec', '-')}")
        print(f"Memory (KB): {stats.get('peak_mem_kb', '-')}")
    print()

    # ── Write output ──────────────────────
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    write_output(solution, output_file)

    print(f"✅ Output written to {output_file}\n")


# ============================================================
# MAIN
# ============================================================

def main():
    for test_id in TEST_IDS:
        try:
            run_one(test_id)
        except Exception as e:
            print(f"[ERROR] Test {test_id} failed: {e}\n")


if __name__ == "__main__":
    main()