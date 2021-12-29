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
        self.mine_squares = []              # List of coordinates of all squares with mines
        self.flag_squares = []              # List of coordinates of all squares with flags

        self.num_committed_mines = 0        # Tracks number of successfully committed mines
        self.num_revealed = 0               # Number of tiles successfully revealed
        self.exploded = False

        # Loop through all grid coordinates to create FieldSquares
        for x in range(width):
            self.field.append([])
            for y in range(height):
                self.field[x].append(FieldSquare(self, x, y))

    def reset(self):
        # Resets grid, spawns new mines based on # mines in current minefield state
        num_mines = len(self.mine_squares) + self.num_committed_mines

        # Reset game-status parameters
        self.num_revealed = 0
        self.num_committed_mines = 0
        self.exploded = False

        # Manually re-establish (without recreating) each field square
        # This is done to not have to re-establish linked buttons
        width, height = self.size
        for x in range(width):
            for y in range(height):
                self.get_square(x, y).__init__(self, x, y)

        # Repopulate mines and reset position tracking
        self.mine_squares = []
        self.flag_squares = []
        self.populate_mines(num_mines)

    def get_square(self, pos_x, pos_y):
        # Return FieldSquare at position described
        if not 0 <= pos_x < self.size[0] or not 0 <= pos_y < self.size[1]:
            return None
        else:
            return self.field[pos_x][pos_y]

    def set_mine(self, pos_x, pos_y):
        # Method to manually set a mine at the desired position
        field_to_set = self.get_square(pos_x, pos_y)
        if field_to_set is not None:
            if not field_to_set.has_mine and self.safe_tiles > 1:
                field_to_set.set_mine()
                self.safe_tiles -= 1

    def populate_mines(self, num_mines=1):
        # Number of mines to auto-populate can be from 0 to 1 less than # of safe tiles
        # (there must be at least one mine to populate)
        num_mines = min(
            max(num_mines, 1),
            self.size[0] * self.size[1] - 1
        )

        # Need to loop through each mine # to populate
        # i is a dummy value and not used in loop
        for i in range(num_mines):
            # Generate random x,y pairs until a non-mined tile is found
            location_found = False
            while not location_found:
                x_to_mine = randint(0, self.size[0] - 1)
                y_to_mine = randint(0, self.size[1] - 1)
                tile_to_mine = self.get_square(x_to_mine, y_to_mine)
                location_found = not tile_to_mine.has_mine

            tile_to_mine.set_mine()
            # Remember coordinates of all generated mines to show mines on game loss
            self.mine_squares.append((x_to_mine, y_to_mine))

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

    def reveal_mines(self):
        # Force-reveals any mine tiles. (And any
        # Only called once user reveals a mine and loses the game
        for mine_pos in self.mine_squares:
            current_mine = self.get_square(mine_pos[0], mine_pos[1])
            current_mine.has_flag = False
            current_mine.is_revealed = True

        for flag_pos in self.flag_squares:
            # Force-reveal flagged non-mine tiles to display X'ed mines on gameover
            current_flag = self.get_square(flag_pos[0], flag_pos[1])
            if not current_flag.has_mine:
                current_flag.is_revealed = True

    def commit_mines(self):
        # A unique functionality for my implementation of minesweeper
        # Removes all successfully flagged mines from map & adjusts neighbor counts
        # Explodes if a non-mined tile is flagged

        # First, check if any flags are non-mined (we don't want to remove any mines until we know this)
        squares_to_commit = []
        for flag_x, flag_y in self.flag_squares:
            flag_square = self.get_square(flag_x, flag_y)
            assert isinstance(flag_square, FieldSquare)

            # Debugging, everything in flag_squares SHOULD have a flag
            assert flag_square.has_flag

            if not flag_square.has_mine:
                self.exploded = True
                self.reveal_mines()
                return
            else:
                squares_to_commit.append(flag_square)

        for square in squares_to_commit:
            square.remove_mine()

    def dig_square(self, x_pos, y_pos):
        # Method to manually reveal a mine via MineField
        # (usually only used during debugging - during game, mines are revealed
        # on the FieldSquare side)

        self.get_square(x_pos, y_pos).dig()
        self.print_minefield()

    def game_state(self):
        # Integer codes indicating state of game
        #   -1  Exploded
        #    0  Still going
        #    1  Game won
        if self.exploded:
            return -1
        elif self.num_revealed >= (self.size[0] * self.size[1] - len(self.mine_squares)):
            # If num tiles revealed >= number of safe tiles
            return 1
        else:
            return 0

    # get_color() and get_text() methods for object-linked buttons
    def get_color(self):
        if self.exploded:
            return (255, 0, 0)
        elif self.num_revealed >= self.safe_tiles:
            return (0, 255, 0)
        else:
            return (100, 100, 100)

    def get_text(self):
        if self.exploded:
            return "You Lost!"
        elif self.num_revealed >= self.safe_tiles:
            return "You Win"
        else:
            return "Game is still in progress."


class FieldSquare:
    # Individual square in minefield
    # Contains flags indicating if square is:
    #   mined
    #   flagged
    #   revealed
    #   exploded
    # Contains methods for digging (and auto-digging blanks around it)
    def __init__(self, containing_field, pos_x, pos_y):
        self.field = containing_field  # Reference to minefield this square is a part of
        self.pos = (pos_x, pos_y)
        self.neighboring_mines = 0  # Number of mines adjacent to this square

        self.has_mine = False  # Boolean flag indicating there is a mine in this field
        self.mine_removed = False  # Indicates if a mine previously here has been removed
        self.has_flag = False  # Indicates if a flag has been set. Flagged tiles can't be revealed
        self.is_revealed = False  # Indicates if tile has been looked into
        self.source_explosion = False # Indicates that this tile caused game-over

    def neighbor(self, dir_x, dir_y):
        # Returns a reference to another FieldSquare in the dirction provides
        return self.field.get_square(
            dir_x + self.pos[0],
            dir_y + self.pos[1]
        )

    def all_neighbors(self):
        # Returns a list of all existing neighboring tiles (All squares one square away, including diagonals)
        to_return = []
        for delta_x in range(-1, 2):
            for delta_y in range(-1, 2):
                if delta_x != 0 or delta_y != 0:
                    neighbor_field = self.neighbor(delta_x, delta_y)
                    if neighbor_field is not None:
                        to_return.append(neighbor_field)
        return to_return

    def set_mine(self):
        self.has_mine = True
        for square in self.all_neighbors():
            square.neighboring_mines += 1

    def remove_mine(self, commit=True):
        # Remove a mine from the field & adjust neighboring mine counts
        # commit parameter indicates whether to display & store that a mine used to be there
        # True: Stores mine_removed flag
        #       Will be indicated visually on screen & not show number underneath
        # False: No flag stored
        #       Square should behave as if there was never a mine there at all
        #       Removes mine without revealing square

        # remove_mine() could/should only be called when tile is flagged & mined
        assert (self.has_flag and self.has_mine)
        self.has_flag = False
        self.has_mine = False
        self.mine_removed = commit

        for n in self.all_neighbors():
            n.neighboring_mines -= 1

        self.field.mine_squares.remove(self.pos)
        self.field.flag_squares.remove(self.pos)

        if commit:
            self.dig()
            self.field.num_committed_mines += 1

            for n in self.all_neighbors():
                # For each revealed 1 that became a 0,
                # un-reveal and re-dig to trigger 0-square auto-revealing for other squares

                if n.is_revealed and n.neighboring_mines == 0 and not n.mine_removed:
                    self.field.num_revealed -= 1
                    n.is_revealed = False
                    n.dig()


    def toggle_flag(self):
        if not self.is_revealed:
            # Reverse "has_flag" flag       ( sorry for the naming confusion here)
            self.has_flag = not self.has_flag

            # Adjust parent field's flag position storage
            if self.has_flag:
                self.field.flag_squares.append(self.pos)
            elif not self.has_flag:
                self.field.flag_squares.remove(self.pos)

    def dig(self, outer=False):
        # Digs on a square to reveal either a mine
        # or a number (indicating # of nearby mines)
        # Includes logic to auto-reveal chunks of 0-neighbor squares
        if not self.has_flag and not self.is_revealed:
            # Reveal if tile is interactable
            # and update parent field's revealed count
            self.is_revealed = True
            self.field.num_revealed += 1
            if self.has_mine:
                # If mine, explode and pass game condition to field
                self.source_explosion = True
                self.field.exploded = True
                self.field.reveal_mines()
            elif self.neighboring_mines == 0:
                # If no neighboring mines, pread the dig around to anything with 0
                # Exclude mine-removed tiles from auto-fill logic
                to_dig = [self]
                while len(to_dig) > 0:
                    for n in to_dig.pop(0).all_neighbors():
                        # Check each neighbor for clickability
                        if not n.has_flag and not n.is_revealed and not n.mine_removed:
                            # Reveal each neighbor and update parent field's revealed count
                            # Exclude mine-removed tiles from reveal logic
                            n.is_revealed = True
                            self.field.num_revealed += 1
                            if n.neighboring_mines == 0:
                                # If neighbor also 0 count, add to list to be considered
                                to_dig.append(n)

    def get_display_text(self):
        # What text to display on printing minefield
        if self.has_mine:
            to_return = "M"
        else:
            to_return = str(self.neighboring_mines)

        if not self.is_revealed:
            to_return = "[" + to_return + "]"

        return to_return

