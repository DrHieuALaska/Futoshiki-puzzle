def check_row(puzzle, r, val):
    """Check row uniqueness"""
    return val not in puzzle.grid[r]


def check_column(puzzle, c, val):
    """Check column uniqueness"""
    for i in range(puzzle.N):
        if puzzle.grid[i][c] == val:
            return False
    return True


def check_horizontal_constraint(puzzle, r, c, val):
    """
    Check constraints between (r,c) and (r,c+1) or (r,c-1)
    """
    # Check right neighbor
    if c < puzzle.N - 1:
        constraint = puzzle.h_constraints[r][c]
        right_val = puzzle.grid[r][c + 1]

        if constraint == 1:  # <
            if right_val != 0 and not (val < right_val):
                return False
        elif constraint == -1:  # >
            if right_val != 0 and not (val > right_val):
                return False

    # Check left neighbor
    if c > 0:
        constraint = puzzle.h_constraints[r][c - 1]
        left_val = puzzle.grid[r][c - 1]

        if constraint == 1:  # left < current
            if left_val != 0 and not (left_val < val):
                return False
        elif constraint == -1:  # left > current
            if left_val != 0 and not (left_val > val):
                return False

    return True


def check_vertical_constraint(puzzle, r, c, val):
    """
    Check constraints between (r,c) and (r+1,c) or (r-1,c)
    """
    # Check below
    if r < puzzle.N - 1:
        constraint = puzzle.v_constraints[r][c]
        down_val = puzzle.grid[r + 1][c]

        if constraint == 1:  # top < bottom
            if down_val != 0 and not (val < down_val):
                return False
        elif constraint == -1:  # top > bottom
            if down_val != 0 and not (val > down_val):
                return False

    # Check above
    if r > 0:
        constraint = puzzle.v_constraints[r - 1][c]
        up_val = puzzle.grid[r - 1][c]

        if constraint == 1:  # up < current
            if up_val != 0 and not (up_val < val):
                return False
        elif constraint == -1:  # up > current
            if up_val != 0 and not (up_val > val):
                return False

    return True


def is_valid(puzzle, r, c, val):
    """
    FULL constraint check (used everywhere)
    """
    return (
        check_row(puzzle, r, val)
        and check_column(puzzle, c, val)
        and check_horizontal_constraint(puzzle, r, c, val)
        and check_vertical_constraint(puzzle, r, c, val)
    )