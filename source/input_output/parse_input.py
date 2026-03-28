from model.puzzle import Puzzle

def parse_input(file_path):
    with open(file_path, 'r') as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")] # Skip empty lines/ comments #

    idx = 0
    N = int(lines[idx]) # Read the first line to get N size of the grid
    idx += 1

    grid = []
    for _ in range(N):
        row = list(map(int, lines[idx].split(',')))
        grid.append(row)
        idx += 1

    h_constraints = []
    for _ in range(N):
        row = list(map(int, lines[idx].split(',')))
        h_constraints.append(row)
        idx += 1

    v_constraints = []
    for _ in range(N - 1):
        row = list(map(int, lines[idx].split(',')))
        v_constraints.append(row)
        idx += 1

    return Puzzle(N, grid, h_constraints, v_constraints)