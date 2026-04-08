import os

from input_output.parse_input import parse_input
from input_output.output_writer import write_output

from search.back_tracking import solve_backtracking
from search.brute_force import brute_force
from search.hybrid_backtracking_with_fc import solve_hybrid_backtracking_with_fc
from search.astar import solve_astar
from search.forward_chaining_solve import forward_chaining_solve
from search.backward_chaining_solve import backward_chaining_solve

from FOL.kb import KnowledgeBase

from inference.sat_checkValid_model import validate_solution


# ============================================================
# USER CONFIG
# ============================================================

ALGORITHM = "astar"   # options: backtracking, astar, bruteforce, forward_chaining, backward_chaining, hybrid_backtracking_with_fc
DIFFICULTY = "hard"   # easy, medium, hard
SIZE = "5x5"          # 4x4 → 5x5, 6x6, 7x7, 8x8, 9x9
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

    elif ALGORITHM == "backward_chaining":
        solution, stats = backward_chaining_solve(puzzle, kb)
        return solution, stats

    elif ALGORITHM == "hybrid_backtracking_with_fc":
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
        if(ALGORITHM == "hybrid_backtracking_with_fc"):
            print(f"Backtracking Fallbacks: {stats.get('bt_fallbacks', '-')}")
        print(f"Time (s)   : {stats.get('time_sec', '-')}")
        print(f"Memory (KB): {stats.get('peak_mem_kb', '-')}")
    print()

    # ── Write output ──────────────────────
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    write_output(solution, output_file)

    # ── Check solution validity ───────────
    is_valid, violations = validate_solution(kb, solution.grid)
    if is_valid:
        print("✅ Solution is valid.")
    else:
        print("❌ Solution is invalid.")
        print("Violations:")
        for clause in violations:
            print(f"  - {clause}")

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