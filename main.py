import time

# This code is written with the help of this page: http://norvig.com/sudoku.html

""" If we represent rows with 'A B C D E F G H I' and columns with '1 2 3 4 5 6 7 8 9', then elements in each smaller
    square can be generated with cross product of rows and columns, like:

    A1 A2 A3| A4 A5 A6| A7 A8 A9
    B1 B2 B3| B4 B5 B6| B7 B8 B9
    C1 C2 C3| C4 C5 C6| C7 C8 C9
   ---------+---------+---------
    D1 D2 D3| D4 D5 D6| D7 D8 D9
    E1 E2 E3| E4 E5 E6| E7 E8 E9
    F1 F2 F3| F4 F5 F6| F7 F8 F9
   ---------+---------+---------
    G1 G2 G3| G4 G5 G6| G7 G8 G9
    H1 H2 H3| H4 H5 H6| H7 H8 H9
    I1 I2 I3| I4 I5 I6| I7 I8 I9
 """

"""
NOTATIONS:
Squares = All entries in a sudoku puzzle. A 9*9 sudoku puzzle has 81 squares
Units = The columns (1-9), the rows (A-I) and each smaller 3*3 box are called units.
Peers = All the squares sharing a unit are called Peers.
"""


def cross(A, B):
    """
    Cross product of elements in A and elements in B
    """
    return [a+b for a in A for b in B]


rows = 'ABCDEFGHI'
columns = '123456789'
digits = columns        # Used later
squares = cross(rows, columns)
unitlist = ([cross(rows, c) for c in columns] +
            [cross(r, columns) for r in rows] +
            [cross(rs, cs) for rs in ('ABC', 'DEF', 'GHI') for cs in ('123', '456', '789')])
units = dict((s, [u for u in unitlist if s in u])
             for s in squares)
peers = dict((s, set(sum(units[s], []))-set([s]))
             for s in squares)


"""
A dict or dictionary is Python's name for a hash table that maps each key to a value; that these are specified as a
sequence of (key, value) tuples; that dict((s, [...]) for s in squares) creates a dictionary which maps each square s 
to a value that is the list [...]; and that the expression [u for u in unitlist if s in u] means that this value is 
the list of units u such that the square s is a member of u. So read this assignment statement as "units is a 
dictionary where each square maps to the list of units that contain the square". Similarly, read the next assignment 
statement as "peers is a dictionary where each square s maps to the set of squares formed by the union of the squares 
in the units of s, but not s itself".
"""


def test():
    """
    A set of unit tests.
    """
    assert len(squares) == 81
    assert len(unitlist) == 27
    assert all(len(units[s]) == 3 for s in squares)
    assert all(len(peers[s]) == 20 for s in squares)
    assert units['C2'] == [['A2', 'B2', 'C2', 'D2', 'E2', 'F2', 'G2', 'H2', 'I2'],
                           ['C1', 'C2', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9'],
                           ['A1', 'A2', 'A3', 'B1', 'B2', 'B3', 'C1', 'C2', 'C3']]
    assert peers['C2'] == set(['A2', 'B2', 'D2', 'E2', 'F2', 'G2', 'H2', 'I2',
                               'C1', 'C3', 'C4', 'C5', 'C6', 'C7', 'C8', 'C9',
                               'A1', 'A3', 'B1', 'B3'])
    print('All tests pass.')


"""
Grid is the name reserved for initial state of the puzzle. Then the puzzle (solved or unsolved) is referred to as
a values collection, because it will give all the remaining possible values for each square. For the textual format 
(grid) we'll allow a string of characters with 1-9 indicating a digit, and a 0 or period specifying an empty square. 
All other characters are ignored (including spaces, newlines, dashes, and bars). So each of the following three grid 
strings represent the same puzzle:

"4.....8.5.3..........7......2.....6.....8.4......1.......6.3.7.5..2.....1.4......"

400000805
030000000
000700000
020000060
000080400
000010000
000603070
500200000
104000000


4 . . |. . . |8 . 5 
. 3 . |. . . |. . . 
. . . |7 . . |. . . 
------+------+------
. 2 . |. . . |. 6 . 
. . . |. 8 . |4 . . 
. . . |. 1 . |. . . 
------+------+------
. . . |6 . 3 |. 7 . 
5 . . |2 . . |. . . 
1 . 4 |. . . |. . . 

A 9*9 array is not useful for values because squares have names like A1 not (0,0).
So, values will be a dict with squares as keys. The value of each key will be the possible digits for that square: a 
single digit if it was given as part of the puzzle definition or if we have figured out what it must be, and a 
collection of several digits if we are still uncertain. So a grid where A1 is 7 and C7 is empty would be represented as 
{'A1': '7', 'C7': '123456789', ...}.
"""


def parse_grid(grid):
    """
    Convert grid to a dict of possible values, {square: digits}, or
    return False if a contradiction is detected.
    """
    # To start, every square can be any digit; then assign values from the grid.
    values = dict((s, digits) for s in squares)
    for s, d in grid_values(grid).items():
        if d in digits and not assign(values, s, d):
            return False  # (Fail if we can't assign d to square s.)
    return values


def grid_values(grid):
    """
    Convert grid into a dict of {square: char} with '0' or '.' for empties.
    """
    chars = [c for c in grid if c in digits or c in '0.']
    assert len(chars) == 81
    return dict(zip(squares, chars))

"""
CONSTRAINT PROPAGATION:

The function parse_grid calls assign(values, s, d). We could implement this as values[s] = d, but we can do more than 
just that. Those with experience solving Sudoku puzzles know that there are two important strategies that we can use to 
make progress towards filling in all the squares:
(1) If a square has only one possible value, then eliminate that value from the square's peers.
(2) If a unit has only one possible place for a value, then put the value there.

As an example of strategy (1) if we assign 7 to A1, yielding {'A1': '7', 'A2':'123456789', ...}, we see that A1 has only
one value, and thus the 7 can be removed from its peer A2 (and all other peers), 
giving us {'A1': '7', 'A2': '12345689', ...}. As an example of strategy (2), if it turns out that none of A3 through 
A9 has a 3 as a possible value, then the 3 must belong in A2, and we can update to {'A1': '7', 'A2':'3', ...}. These 
updates to A2 may in turn cause further updates to its peers, and the peers of those peers, and so on. This process is 
called constraint propagation.
The function assign(values, s, d) will return the updated values (including the updates from constraint propagation), 
but if there is a contradiction--if the assignment cannot be made consistently--then assign returns False. 

For example, if a grid starts with the digits '77...' then when we try to assign the 7 to A2, assign would notice 
that 7 is not a possibility for A2, because it was eliminated by the peer, A1.

It turns out that the fundamental operation is not assigning a value, but rather eliminating one of the possible 
values for a square, which we implement with eliminate(values, s, d). Once we have eliminate, 
then assign(values, s, d) can be defined as "eliminate all the values from s except d".
"""


def assign(values, s, d):
    """
    Eliminate all the other values (except d) from values[s] and propagate.
    Return values, except return False if a contradiction is detected.
    """
    other_values = values[s].replace(d, '')
    if all(eliminate(values, s, d2) for d2 in other_values):
        return values
    else:
        return False


def eliminate(values, s, d):
    """
    Eliminate d from values[s]; propagate when values or places <= 2.
    Return values, except return False if a contradiction is detected.
    """
    if d not in values[s]:
        return values   # Already eliminated
    values[s] = values[s].replace(d,'')
    # (1) If a square s is reduced to one value d2, then eliminate d2 from the peers.
    if len(values[s]) == 0:
        return False    # Contradiction: removed last value
    elif len(values[s]) == 1:
        d2 = values[s]
        if not all(eliminate(values, s2, d2) for s2 in peers[s]):
            return False
    # (2) If a unit u is reduced to only one place for a value d, then put it there.
    for u in units[s]:
        dplaces = [s for s in u if d in values[s]]
    if len(dplaces) == 0:
        return False    # Contradiction: no place for this value
    elif len(dplaces) == 1:
        # d can only be in one place in unit; assign it there
            if not assign(values, dplaces[0], d):
                return False
    return values


def display(values):
    """
    Display these values as a 2-D grid.
    """
    width = 1+max(len(values[s]) for s in squares)
    line = '+'.join(['-'*(width*3)]*3)
    for r in rows:
        print(''.join(values[r+c].center(width)+('|' if c in '36' else '')) for c in columns)
        if r in 'CF':
            print(line)
    print("")


def solve(grid): return search(parse_grid(grid))


def search(values):
    """
    Using depth-first search and propagation, try all possible values.
    """
    if values is False:
        return False  # Failed earlier
    if all(len(values[s]) == 1 for s in squares):
        return values  # Solved!
    # Chose the unfilled square s with the fewest possibilities
    n, s = min((len(values[s]), s) for s in squares if len(values[s]) > 1)
    return some(search(assign(values.copy(), s, d)) for d in values[s])


def some(seq):
    """
    Return some element of seq that is true.
    """
    for e in seq:
        if e:
            return e
    return False


def solve_all(grids, name='', showif=0.0):
    """
    Attempt to solve a sequence of grids. Report results.
    When showif is a number of seconds, display puzzles that take longer.
    When showif is None, don't display any puzzles.
    """
    def time_solve(grid):
        start = time.clock()
        values = solve(grid)
        t = time.clock()-start
        # Display puzzles that take long enough
        if showif is not None and t > showif:
            display(grid_values(grid))
            if values: display(values)
            print('(%.2f seconds)\n' % t)
        return (t, solved(values))

    times, results = list(zip(*[time_solve(grid) for grid in grids]))
    N = len(grids)
    if N > 1:
        print("Solved %d of %d %s puzzles (avg %.2f secs (%d Hz), max %.2f secs)." % (
            sum(results), N, name, sum(times)/N, N/sum(times), max(times)))


def some(seq):
    "Return some element of seq that is true."
    for e in seq:
        if e: return e
    return False


def from_file(filename, sep='\n'):
    "Parse a file into a list of strings, separated by sep."
    return open(filename).read().strip().split(sep)


def solved(values):
    """
    A puzzle is solved if each unit is a permutation of the digits 1 to 9.
    """
    def unitsolved(unit): return set(values[s] for s in unit) == set(digits)
    return values is not False and all(unitsolved(unit) for unit in unitlist)


if __name__ == "__main__":
    test()
    solve_all(from_file("easy50.txt"), "easy", None)
    solve_all(from_file("top95.txt"), "hard", None)
    solve_all(from_file("hardest.txt"), "hardest", None)
    solve_all(from_file("insane.txt"), "hardest", None)
