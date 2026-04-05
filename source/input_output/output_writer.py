def write_output(puzzle, file_path):
    lines = _format_puzzle(puzzle)
    with open(file_path, "w") as f:
        for line in lines:
            f.write(line + "\n")
    for line in lines:
        print(line)


def _format_puzzle(puzzle):
    lines = []
    N = puzzle.N

    for r in range(N):
        # Value row with inline horizontal constraints
        row_parts = []
        for c in range(N):
            row_parts.append(str(puzzle.grid[r][c]))
            if c < N - 1:
                h = puzzle.h_constraints[r][c]
                if h == 1:      row_parts.append("<")
                elif h == -1:   row_parts.append(">")
                else:           row_parts.append(" ")
        lines.append(" ".join(row_parts))

        # Vertical constraint row between this row and the next
        if r < N - 1:
            vert_parts = []
            for c in range(N):
                v = puzzle.v_constraints[r][c]
                if v == 1:      vert_parts.append("^")   # top < bottom
                elif v == -1:   vert_parts.append("v")   # top > bottom
                else:           vert_parts.append(" ")
                if c < N - 1:
                    vert_parts.append(" ")               # spacer to align under cells
            lines.append(" ".join(vert_parts))

    return lines