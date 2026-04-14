import argparse
import csv
import io
from contextlib import nullcontext, redirect_stdout
from pathlib import Path
from statistics import mean
from time import perf_counter

from FOL.kb import KnowledgeBase
from inference.sat_checkValid_model import validate_solution
from input_output.parse_input import parse_input
from search.astar import solve_astar

# Usage:
# python3 source/benchmark_astar.py
# python3 source/benchmark_astar.py --difficulty easy --size 4x4 --test-ids 02 --heuristics combined --prunings fc,ac3
# python3 source/benchmark_astar.py --difficulty medium --size 5x5 --test-ids all --heuristics combined,remaining_cells --prunings ac3 --repeat 3 --csv /tmp/astar_benchmark.csv

BASE_DIR = Path(__file__).resolve().parent
INPUT_ROOT = BASE_DIR / "Inputs"
VALID_HEURISTICS = ("remaining_cells", "inequality_chains", "combined")
VALID_PRUNINGS = ("fc", "ac3")
DEFAULT_PRUNINGS = ("fc", "ac3")


def parse_args():
    parser = argparse.ArgumentParser(
        description="Benchmark A* on the Futoshiki input corpus."
    )
    parser.add_argument(
        "--difficulty",
        default="easy",
        choices=("easy", "medium", "hard"),
        help="Input difficulty folder to benchmark.",
    )
    parser.add_argument(
        "--size",
        default="4x4",
        choices=("4x4", "6x6",  "8x8"),
        help="Board size folder to benchmark.",
    )
    parser.add_argument(
        "--test-ids",
        default="01",
        help="Comma-separated input ids such as 01,02,03. Use 'all' to run every file in the folder.",
    )
    parser.add_argument(
        "--heuristics",
        default="combined",
        help="Comma-separated A* heuristics to benchmark.",
    )
    parser.add_argument(
        "--prunings",
        default=",".join(DEFAULT_PRUNINGS),
        help="Comma-separated pruning methods to benchmark.",
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=1,
        help="How many times to run each benchmark case.",
    )
    parser.add_argument(
        "--csv",
        dest="csv_path",
        default=None,
        help="Optional CSV file path to export detailed results.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Keep the internal A* logging instead of silencing it.",
    )
    return parser.parse_args()


def parse_csv_arg(raw_value):
    values = [value.strip() for value in raw_value.split(",") if value.strip()]
    if not values:
        raise ValueError("Expected at least one comma-separated value.")
    return values


def discover_input_files(difficulty, size, requested_ids):
    input_dir = INPUT_ROOT / difficulty / size
    if not input_dir.exists():
        raise FileNotFoundError(f"Input folder not found: {input_dir}")

    if requested_ids == "all":
        return sorted(input_dir.glob("input-*.txt"))

    wanted = {test_id.strip() for test_id in requested_ids.split(",") if test_id.strip()}
    files = []
    for test_id in sorted(wanted):
        path = input_dir / f"input-{test_id}.txt"
        if not path.exists():
            raise FileNotFoundError(f"Input file not found: {path}")
        files.append(path)
    return files


def extract_test_id(input_path):
    stem = input_path.stem
    return stem.split("-")[-1]


def run_astar_case(input_path, heuristic, pruning, verbose):
    puzzle = parse_input(str(input_path))
    kb = KnowledgeBase(puzzle)

    stdout_context = nullcontext() if verbose else redirect_stdout(io.StringIO())
    start = perf_counter()
    try:
        with stdout_context:
            solution, stats = solve_astar(
                puzzle, kb, heuristic=heuristic, pruning=pruning
            )
    except Exception as exc:
        return {
            "solved": False,
            "valid": False,
            "wall_sec": round(perf_counter() - start, 6),
            "solver_time_sec": None,
            "peak_mem_kb": None,
            "expansions": None,
            "generated": None,
            "error": str(exc),
        }

    wall_sec = round(perf_counter() - start, 6)
    is_valid = False
    if solution is not None:
        is_valid, _ = validate_solution(kb, solution.grid)

    return {
        "solved": solution is not None,
        "valid": is_valid,
        "wall_sec": wall_sec,
        "solver_time_sec": stats.get("time_sec"),
        "peak_mem_kb": stats.get("peak_mem_kb"),
        "expansions": stats.get("expansions"),
        "generated": stats.get("generated"),
        "error": "",
    }


def run_case_repeated(input_path, heuristic, pruning, repeat, verbose):
    runs = [
        run_astar_case(input_path, heuristic, pruning, verbose)
        for _ in range(repeat)
    ]

    errors = [run["error"] for run in runs if run["error"]]
    if errors:
        return {
            "input": input_path.name,
            "test_id": extract_test_id(input_path),
            "heuristic": heuristic,
            "pruning": pruning,
            "repeat": repeat,
            "solved": False,
            "valid": False,
            "wall_sec": round(mean(run["wall_sec"] for run in runs), 6),
            "solver_time_sec": None,
            "peak_mem_kb": None,
            "expansions": None,
            "generated": None,
            "error": errors[0],
        }

    return {
        "input": input_path.name,
        "test_id": extract_test_id(input_path),
        "heuristic": heuristic,
        "pruning": pruning,
        "repeat": repeat,
        "solved": all(run["solved"] for run in runs),
        "valid": all(run["valid"] for run in runs),
        "wall_sec": round(mean(run["wall_sec"] for run in runs), 6),
        "solver_time_sec": round(mean(run["solver_time_sec"] for run in runs), 6),
        "peak_mem_kb": round(mean(run["peak_mem_kb"] for run in runs), 2),
        "expansions": round(mean(run["expansions"] for run in runs), 2),
        "generated": round(mean(run["generated"] for run in runs), 2),
        "error": "",
    }


def format_value(value):
    if value is None:
        return "-"
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value)


def print_table(rows):
    headers = (
        "test_id",
        "heuristic",
        "pruning",
        "solved",
        "valid",
        "wall_sec",
        "solver_time_sec",
        "expansions",
        "generated",
        "peak_mem_kb",
        "error",
    )
    widths = {
        header: max(
            len(header),
            *(len(format_value(row.get(header))) for row in rows)
        )
        for header in headers
    }

    header_line = "  ".join(f"{header:<{widths[header]}}" for header in headers)
    separator = "  ".join("-" * widths[header] for header in headers)
    print(header_line)
    print(separator)
    for row in rows:
        print(
            "  ".join(
                f"{format_value(row.get(header)):<{widths[header]}}"
                for header in headers
            )
        )


def print_summary(rows):
    summary = {}
    for row in rows:
        if row["error"]:
            continue
        key = (row["heuristic"], row["pruning"])
        summary.setdefault(key, []).append(row)

    if not summary:
        return

    print("\nAverages by configuration")
    summary_rows = []
    for (heuristic, pruning), config_rows in sorted(summary.items()):
        summary_rows.append(
            {
                "heuristic": heuristic,
                "pruning": pruning,
                "cases": len(config_rows),
                "avg_wall_sec": round(mean(row["wall_sec"] for row in config_rows), 6),
                "avg_solver_time_sec": round(
                    mean(row["solver_time_sec"] for row in config_rows), 6
                ),
                "avg_expansions": round(mean(row["expansions"] for row in config_rows), 2),
                "avg_generated": round(mean(row["generated"] for row in config_rows), 2),
                "avg_peak_mem_kb": round(
                    mean(row["peak_mem_kb"] for row in config_rows), 2
                ),
            }
        )

    headers = (
        "heuristic",
        "pruning",
        "cases",
        "avg_wall_sec",
        "avg_solver_time_sec",
        "avg_expansions",
        "avg_generated",
        "avg_peak_mem_kb",
    )
    widths = {
        header: max(
            len(header),
            *(len(str(row[header])) for row in summary_rows)
        )
        for header in headers
    }

    header_line = "  ".join(f"{header:<{widths[header]}}" for header in headers)
    separator = "  ".join("-" * widths[header] for header in headers)
    print(header_line)
    print(separator)
    for row in summary_rows:
        print(
            "  ".join(f"{str(row[header]):<{widths[header]}}" for header in headers)
        )


def write_csv(rows, csv_path):
    output_path = Path(csv_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "test_id",
        "input",
        "heuristic",
        "pruning",
        "repeat",
        "solved",
        "valid",
        "wall_sec",
        "solver_time_sec",
        "expansions",
        "generated",
        "peak_mem_kb",
        "error",
    ]
    with output_path.open("w", newline="") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    args = parse_args()

    if args.repeat < 1:
        raise ValueError("--repeat must be at least 1.")

    heuristics = parse_csv_arg(args.heuristics)
    prunings = parse_csv_arg(args.prunings)
    unknown_heuristics = sorted(set(heuristics) - set(VALID_HEURISTICS))
    unknown_prunings = sorted(set(prunings) - set(VALID_PRUNINGS))
    if unknown_heuristics:
        raise ValueError(
            "Unknown heuristic(s): "
            f"{', '.join(unknown_heuristics)}. "
            f"Choose from {', '.join(VALID_HEURISTICS)}."
        )
    if unknown_prunings:
        raise ValueError(
            "Unknown pruning method(s): "
            f"{', '.join(unknown_prunings)}. "
            f"Choose from {', '.join(VALID_PRUNINGS)}."
        )
    input_files = discover_input_files(args.difficulty, args.size, args.test_ids)

    print(
        f"Benchmarking A* on {args.difficulty}/{args.size} "
        f"for {len(input_files)} input(s), {len(heuristics)} heuristic(s), "
        f"{len(prunings)} pruning method(s), repeat={args.repeat}"
    )

    rows = []
    for input_path in input_files:
        for heuristic in heuristics:
            for pruning in prunings:
                row = run_case_repeated(
                    input_path, heuristic, pruning, args.repeat, args.verbose
                )
                rows.append(row)

    print()
    print_table(rows)
    print_summary(rows)

    if args.csv_path:
        write_csv(rows, args.csv_path)
        print(f"\nDetailed CSV written to {Path(args.csv_path).resolve()}")


if __name__ == "__main__":
    main()
