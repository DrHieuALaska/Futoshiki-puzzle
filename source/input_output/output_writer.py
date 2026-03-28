def write_output(puzzle, file_path):
    with open(file_path, "w") as f:
        for row in puzzle.grid:
            line = " ".join(map(str, row))
            f.write(line + "\n")