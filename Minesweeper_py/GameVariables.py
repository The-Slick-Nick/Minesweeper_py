from random import randint
import time


class MineField:
    # Collector of squares in minefield
    # Handles creation of minefield and current state of game
    # (win, loss, etc.)
    def __init__(self, width, height=0):
        if height <= 0:
            height = width
        self.size = (width, height)
        self.field = []                     # Container for all FieldSquares (list of lists)
        self.mine_squares = set()           # Set of coordinates of all squares with mines
        self.flag_squares = set()           # Set of coordinates of all squares with flags

        self.num_committed_mines = 0        # Tracks number of successfully committed mines
        self.num_revealed = 0               # Number of tiles successfully revealed
        self.exploded = False

        # Loop through all grid coordinates to create FieldSquares
        for x in range(width):
            self.field.append([])
            for y in range(height):
                self.field[x].append(FieldSquare(x, y))

    def reset(self, num_mines=-1):
        # Resets grid, spawns new mines based on # mines in current minefield state
        if num_mines < 1:
            num_mines = len(self.mine_squares) + self.num_committed_mines

        self.__init__(self.size[0], self.size[1])
        self.populate_mines(num_mines)

    def out_of_bounds(self, pos_x, pos_y):
        return not (0 <= pos_x < self.size[0] and 0 <= pos_y < self.size[1])

    def get_square(self, pos_x, pos_y):
        # Return FieldSquare at position described
        if self.out_of_bounds(pos_x, pos_y):
            return None
        else:
            return self.field[pos_x][pos_y]

    def set_mine(self, pos_x=-1, pos_y=-1, by_square=None):
        # Attempts to set a mine at the target coordinates, and returns
        # a boolean indicating if it was successful
        if by_square is not None:
            pos_x, pos_y = by_square.pos

        to_return = False
        if not self.out_of_bounds(pos_x, pos_y):
            square_to_set = self.get_square(pos_x, pos_y)
            assert isinstance(square_to_set, FieldSquare)
            if square_to_set.is_clickable() and not square_to_set.has_mine:
                to_return = True
                self.mine_squares.add((pos_x, pos_y))
                square_to_set.set_mine()

                # Increment nearby-mine counter for all neighbors
                for neighbor in self.all_neighbors(pos_x, pos_y):
                    assert isinstance(neighbor, FieldSquare)
                    neighbor.neighboring_mines += 1
        return to_return

    def populate_mines(self, num_mines=1):

        # 1 <= num_mines < safe_tiles
        num_mines = min(
            max(num_mines, 1),
            self.num_safe_tiles() - 1
        )

        # Need to loop through each mine # to populate
        # i is a dummy value and not used in loop
        for i in range(num_mines):
            # Generate random x,y pairs until a non-mined tile is found
            location_found = False
            while not location_found:
                x_to_mine = randint(0, self.size[0] - 1)
                y_to_mine = randint(0, self.size[1] - 1)

                # Sets mine and exits while if successful
                # Does thing and continues while loop if this fails
                location_found = self.set_mine(x_to_mine, y_to_mine)

    def reveal_mines(self):
        # Force-reveals any mine tiles.
        # Typically only called once a user reveals a mine and loses the game
        for mine_pos in self.mine_squares:
            current_mine = self.get_square(mine_pos[0], mine_pos[1])
            # Force remove has_flag flag (even if it was already false)
            current_mine.has_flag = False
            # Force-add the is_revealed flag
            current_mine.is_revealed = True

        for flag_pos in self.flag_squares:
            # Force-reveal flagged non-mine tiles to display X'ed mines on gameover
            if flag_pos not in self.mine_squares:
                self.get_square(flag_pos[0], flag_pos[1]).is_revealed = True

    def commit_mines(self):
        # A unique functionality for my implementation of minesweeper
        # Removes all successfully flagged mines from map & adjusts neighbor counts
        # Explodes if a non-mined tile is flagged

        # First, check if any flags are non-mined (we don't want to remove any mines until we know this)
        to_commit = set()
        for flag_pos in self.flag_squares:
            if flag_pos not in self.mine_squares:
                self.exploded = True
                self.reveal_mines()
                return
            else:
                # Commit flag squares that have a mine
                to_commit.add(self.get_square(flag_pos[0], flag_pos[1]))
        self.remove_mine(by_square=to_commit, commit=True)

    def remove_mine(self, x_pos=-1, y_pos=-1, by_square=None, commit=True):
        if by_square is None:
            square_to_remove = {self.get_square(x_pos, y_pos)}
        else:
            try:
                square_to_remove = set(by_square)
            except TypeError:
                square_to_remove = {by_square}

        new_blanks = set()
        for square in square_to_remove:

            if square.remove_mine(commit):
                # Only run removal logic if a mine was actually removed
                if commit:
                    self.num_committed_mines += 1
                    if square.has_flag:
                        # We only need to remove flag (& flagged tile from flag list) if committing
                        self.toggle_flag(by_square=square)

                    # Main philosophy here: anything dealt with (and thus non-interactable)
                    # should be considered "Revealed"
                    square.is_revealed = True
                    self.num_revealed += 1

                self.mine_squares.remove(square.pos)
                for neighbor in self.all_neighbors(by_square=square):
                    assert isinstance(neighbor, FieldSquare)
                    neighbor.neighboring_mines -= 1
                    if neighbor.is_revealed:
                        # Any square already revealed must now be re-evaluated for blank filling
                        new_blanks.add(neighbor)

        self.spread_blanks(by_square=new_blanks)

    def dig(self, x_pos=-1, y_pos=-1, by_square=None):
        if by_square is not None:
            square_to_dig = by_square
        else:
            square_to_dig = self.get_square(x_pos, y_pos)

        if square_to_dig is not None and square_to_dig.is_clickable():
            square_to_dig.dig()
            self.num_revealed += 1
            if square_to_dig.has_mine:
                self.exploded = True
                self.reveal_mines()
            else:
                self.spread_blanks(by_square=square_to_dig)

    def spread_blanks(self, x_pos=-1, y_pos=-1, by_square=None):
        # Continually reveals neighboring squares so long as the square to consider has 0 neighboring mines
        if by_square is None:
            to_consider = {self.get_square(x_pos, y_pos)}
        else:
            try:
                to_consider = set(by_square)
            except TypeError:
                to_consider = {by_square}

        st = time.time()
        # Keep a running set of tiles to consider
        # Keep removing them & considering new ones them until the set is empty
        while len(to_consider) > 0:
            # Consider & remove an item in the set
            current_square = to_consider.pop()
            if current_square.neighboring_mines == 0:
                # add new squares to consider only if the current one is not next to any mines
                for neighbor in self.all_neighbors(by_square=current_square):
                    if neighbor.is_clickable():
                        neighbor.dig()
                        self.num_revealed += 1
                        to_consider.add(neighbor)

    def toggle_flag(self, x_pos=-1, y_pos=-1, by_square=None):
        if by_square is not None:
            square_to_toggle = by_square
        else:
            square_to_toggle = self.get_square(x_pos, y_pos)

        if square_to_toggle is not None and not square_to_toggle.is_revealed:
            square_to_toggle.toggle_flag()
            if square_to_toggle.has_flag:
                self.flag_squares.add(square_to_toggle.pos)
            else:
                self.flag_squares.remove(square_to_toggle.pos)

    def game_state(self):
        # Integer codes indicating state of game
        #   -1  Exploded
        #    0  Still going
        #    1  Game won
        if self.exploded:
            return -1
        elif self.num_revealed >= self.num_safe_tiles():
            # If num tiles revealed >= number of safe tiles
            return 1
        else:
            return 0

    def num_safe_tiles(self):
        return self.size[0] * self.size[1] - len(self.mine_squares)

    def all_neighbors(self, square_x=-1, square_y=-1, by_square=None):
        if by_square is not None:
            square_x, square_y = by_square.pos

        to_return = []

        for delta_x in range(-1, 2):
            for delta_y in range(-1, 2):
                if delta_x != 0 or delta_y != 0:
                    neighbor_field = self.get_square(square_x + delta_x, square_y + delta_y)
                    if neighbor_field is not None:
                        to_return.append(neighbor_field)
        return to_return

    def print_minefield(self, cushion=5):
        # Prints the status of each mine tile to console
        # brackets [] indicate unrevealed squares
        # M -  mine
        # F -  flag
        # # -  number of neighboring tiles with mines

        print_list = ["" for y in range(self.size[1])]

        # First find the maximum element length to ensure we align everything equally
        max_elem_len = 0
        for x in range(self.size[0]):
            x_list = self.field[x]
            for y in range(self.size[1]):
                y_elem = x_list[y]
                elem_len = len(str(y_elem.get_display_text()))
                if elem_len > max_elem_len:
                    max_elem_len = elem_len

        for x in range(self.size[0]):
            x_list = self.field[x]
            for y in range(self.size[1]):
                y_elem = x_list[y]
                elem_text = y_elem.get_display_text()
                print_list[y] = print_list[y] + elem_text + " " * (cushion + max_elem_len - len(elem_text))

        for str_to_print in print_list:
            print(str_to_print)


class FieldSquare:
    # Individual square in minefield
    # Contains flags indicating if square is:
    #   mined
    #   flagged
    #   revealed
    #   exploded
    # Contains methods for digging (and auto-digging blanks around it)
    def __init__(self, pos_x, pos_y):
        self.pos = (pos_x, pos_y)
        self.neighboring_mines = 0  # Number of mines adjacent to this square

        self.has_mine = False  # Boolean flag indicating there is a mine in this field
        self.mine_removed = False  # Indicates if a mine previously here has been removed
        self.has_flag = False  # Indicates if a flag has been set. Flagged tiles can't be revealed
        self.is_revealed = False  # Indicates if tile has been looked into
        self.source_explosion = False # Indicates that this tile caused game-over

    def is_clickable(self):
        return not (self.is_revealed or self.has_flag or self.mine_removed)

    def set_mine(self):
        self.has_mine = True

    def remove_mine(self, commit=True):
        if self.has_mine:
            self.has_mine = False
            if commit:
                self.mine_removed = True
            return True
        else:
            # Return False if unsuccessful: (no mine there)
            return False

    def toggle_flag(self):
        self.has_flag = not self.has_flag

    def dig(self):
        self.is_revealed = True
        if self.has_mine:
            self.source_explosion = True

    def get_display_text(self):
        # What text to display on printing minefield
        if self.mine_removed:
            to_return = "C"
        elif self.has_flag:
            to_return = "F"
        elif self.has_mine:
            to_return = "M"
        else:
            to_return = str(self.neighboring_mines)

        if not self.is_revealed:
            to_return = "[" + to_return + "]"

        return to_return

