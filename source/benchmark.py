"""
Runs the configured solving algorithms on every test case and reports:
  • Running time (seconds)
  • Peak heap memory (KB)
  • Number of inferences / node expansions

Algorithms compared
-------------------
  1. Brute Force           – blind recursive backtracking, no heuristic
  2. Backtracking (MRV)    – backtracking with Minimum Remaining Values
  3. Hybrid BT + FC        – MRV backtracking + forward-chaining propagation
  4. A* (AC-3 h)                 – original AC-3 look-ahead heuristic
  5. A* (remaining cells h)      – count unresolved cells directly
  6. A* (inequality chains h)    – cover unresolved inequality chains
"""

import sys
import os
import time
import tracemalloc

sys.path.insert(0, os.path.dirname(__file__))

from input_output.parse_input import parse_input

# ── existing solvers (no built-in stats) ──────────────────────────────────────
from search.brute_force import brute_force as _brute_force_raw
from search.back_tracking import solve_backtracking as _backtracking_raw
from search.hybrid_backtracking_with_fc import solve_hybrid_backtracking_with_fc as _hybrid_raw

# ── A* (has built-in stats) ───────────────────────────────────────────────────
from search.astar import solve_astar


# ─────────────────────────────────────────────────────────────────────────────
# Instrumented wrappers for legacy solvers
# ─────────────────────────────────────────────────────────────────────────────

def _run_with_stats(fn, puzzle):
    """
    Wrap a solver that returns (solution | None) with timing and memory
    tracking.  Returns (solution, stats_dict).
    """
    tracemalloc.start()
    t0 = time.perf_counter()
    solution = fn(puzzle.copy())
    elapsed = time.perf_counter() - t0
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    stats = {
        'time_sec': round(elapsed, 6),
        'peak_mem_kb': round(peak / 1024, 2),
        'expansions': 'N/A',   # not tracked by these solvers
        'generated': 'N/A',
    }
    return solution, stats


def run_brute_force(puzzle):
    return _run_with_stats(_brute_force_raw, puzzle)


def run_backtracking(puzzle):
    return _run_with_stats(_backtracking_raw, puzzle)


def run_hybrid(puzzle):
    return _run_with_stats(_hybrid_raw, puzzle)


def run_astar_ac3(puzzle):
    solution, stats = solve_astar(puzzle.copy(), heuristic="ac3")
    return solution, stats


def run_astar_remaining_cells(puzzle):
    solution, stats = solve_astar(
        puzzle.copy(),
        heuristic="remaining_unassigned_cells",
    )
    return solution, stats


def run_astar_inequality_chains(puzzle):
    solution, stats = solve_astar(
        puzzle.copy(),
        heuristic="inequality_chains",
    )
    return solution, stats


# ─────────────────────────────────────────────────────────────────────────────
# Test-case table
# ─────────────────────────────────────────────────────────────────────────────

TEST_CASES = [
    # ("01", "source/Inputs/input-01.txt", "4×4 partial constraints, 4 givens"),
    # ("02", "source/Inputs/input-02.txt", "4×4 all constraints,    4 givens"),
    # ("03", "source/Inputs/input-03.txt", "4×4 all constraints,    2 givens (easy)"),
    # ("04", "source/Inputs/input-04.txt", "4×4 all constraints,    0 givens (pure propagation)"),
    # ("05", "source/Inputs/input-05.txt", "4×4 Solution-B, all h+v, 2 givens"),
    # ("06", "source/Inputs/input-06.txt", "4×4 Solution-B, all h+v, 0 givens"),
    # ("07", "source/Inputs/input-07.txt", "4×4 sparse constraints, 6 givens (BT stress)"),
    # ("08", "source/Inputs/input-08.txt", "5×5 cyclic solution,    3 givens"),
    # ("09", "source/Inputs/input-09.txt", "5×5 cyclic, all constraints, 0 givens"),
    # ("10", "source/Inputs/input-10.txt", "5×5 Solution-D, all constraints, 3 givens"),
    ("11", "source/Inputs/input-11.txt", "9x9"),
    # ("12", "source/Inputs/input-12.txt", "9x9"),
]

SOLVERS = [
    # ("Brute Force",   run_brute_force),
    ("Backtracking",  run_backtracking),
    ("Hybrid BT+FC",  run_hybrid),
    ("A* (AC-3 h)",   run_astar_ac3),
    ("A* (cells h)",  run_astar_remaining_cells),
    ("A* (chains h)", run_astar_inequality_chains),
]


# ─────────────────────────────────────────────────────────────────────────────
# Pretty-printer helpers
# ─────────────────────────────────────────────────────────────────────────────

def _fmt(v, width=10):
    if isinstance(v, float):
        return f"{v:.6f}".rjust(width)
    return str(v).rjust(width)


def _print_header():
    cols = ["Case", "Solver", "Solved", "Time (s)", "Mem (KB)", "Expansions", "Generated"]
    widths = [4, 16, 6, 12, 10, 12, 12]
    header = "  ".join(c.ljust(w) for c, w in zip(cols, widths))
    sep = "  ".join("-" * w for w in widths)
    print(header)
    print(sep)


def _print_row(case_id, solver_name, solved, stats):
    cols = [
        case_id.ljust(4),
        solver_name.ljust(16),
        ("YES" if solved else "NO ").ljust(6),
        _fmt(stats['time_sec'], 12),
        _fmt(stats['peak_mem_kb'], 10),
        _fmt(stats['expansions'], 12),
        _fmt(stats.get('generated', 'N/A'), 12),
    ]
    print("  ".join(cols))


# ─────────────────────────────────────────────────────────────────────────────
# Main benchmark loop
# ─────────────────────────────────────────────────────────────────────────────

def run_benchmark():
    print("=" * 80)
    print("  FUTOSHIKI SOLVER – BENCHMARK RESULTS")
    print("=" * 80)
    print()

    summary = []   # (case_id, solver_name, solved, stats)

    for case_id, path, description in TEST_CASES:
        print(f"-- Test {case_id}: {description}")

        try:
            puzzle = parse_input(path)
        except Exception as e:
            print(f"   [SKIP] Could not load {path}: {e}")
            print()
            continue

        for solver_name, solver_fn in SOLVERS:
            try:
                solution, stats = solver_fn(puzzle)
                solved = solution is not None
            except Exception as e:
                solved = False
                stats = {'time_sec': 0.0, 'peak_mem_kb': 0.0,
                         'expansions': 'ERR', 'generated': 'ERR'}
                print(f"   [{solver_name}] ERROR: {e}")

            summary.append((case_id, solver_name, solved, stats))

        print()

    # ── Summary table ──────────────────────────────────────────────────────
    print()
    print("=" * 80)
    print("  SUMMARY TABLE")
    print("=" * 80)
    print()
    _print_header()

    prev_case = None
    for case_id, solver_name, solved, stats in summary:
        if prev_case is not None and prev_case != case_id:
            print()       # blank line between cases
        _print_row(case_id, solver_name, solved, stats)
        prev_case = case_id

    print()
    print("Notes:")
    print("  • Expansions / Generated are tracked only for A* (others report N/A).")
    print("  • Memory = peak heap allocation during the solver call (tracemalloc).")
    print("  • Time  = wall-clock via time.perf_counter().")
    print()


if __name__ == "__main__":
    run_benchmark()
