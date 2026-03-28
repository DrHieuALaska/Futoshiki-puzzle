def brute_force(puzzle):
    
    # Backtracking search (recursive)
    def solve(cells, idx):
        if idx == len(cells): return True
        r, c = cells[idx]
        for val in puzzle.domain(): # order: 1,2,...N
            if puzzle.is_valid_assignment(r, c, val):
                puzzle.set(r, c, val)
                if solve(cells, idx+1): return True
                puzzle.unset(r, c)
        return False
    
    # Get list of empty cells of the grid
    empty = puzzle.get_empty_cells()
    if solve(empty, 0):
        return puzzle
    return None