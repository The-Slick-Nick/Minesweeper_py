import pygame
from GameVariables import *
from GameInstance import *
import math
pygame.init()

# Display & interacion elements
# Used as a mediator between game objects & the player

### INTERACTABLES ###


class Interactable:
    # Template for any type of on-screen interactable element
    # Stores:
    #   position (pos_x, pos_y)
    #   size (width, height)
    #   functions (leftclick, middleclick, rightclick)
    #   mouse position (mouse_x, mouse_y)
    #   mouse states (old & new pressed as a 3-tuple)
    #   held timers (3, one for each mouse button)
    #   repeat timer (list of tuples - acts as timesheet for button-hold logic)
    # as well as storing mouse positions and button states
    def __init__(self,
                 pos_x=0, pos_y=0,
                 width=-1, height=-1,
                 leftclick=None, middleclick=None, rightclick=None,
                 repeat_timer=None,
                 **kwds):
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.width = width
        self.height = height

        self.mouse_pos = (-1, -1)
        self.old_pressed = (False, False, False)    # Mouse pressed state last time this was checked
        self.new_pressed = (False, False, False)    # Current state of mouse buttons
        self.held_timer = [0, 0, 0]                 # Time (in ticks) that a given button is held down
        self.repeat_timer = repeat_timer            # List of tuples: stores how repeat-pressing works when held down

        # example: repeat_timer = [(60, 30), (90, 15), (30, 2)]
        # For the first 60 ticks a button is held, nothing happens (except for initial click)
        # For the next 90 ticks, button press is done every 30 ticks
        # For the next 30 ticks, button press is done every 15 ticks
        # Button press is done every 2 ticks from then on (until button is let go)

        self.default_leftclick = leftclick
        self.default_middleclick = middleclick
        self.default_rightclick = rightclick

    def leftclick(self):
        if self.default_leftclick is not None:
            self.default_leftclick()

    def middleclick(self):
        if self.default_middleclick is not None:
            self.default_middleclick()

    def rightclick(self):
        if self.default_rightclick is not None:
            self.default_rightclick()

    def store_inputs(self, mouse_pos=(-1, -1), mouse_buttons=(False, False, False)):
        # Stores button states for this iteration
        self.mouse_pos = mouse_pos
        self.old_pressed = self.new_pressed
        self.new_pressed = mouse_buttons

    def mouse_collision(self):
        # Checking if current mouse pos collides with element
        if self.get_rect() is None:
            return False
        else:
            return self.get_rect().collidepoint(self.mouse_pos)

    def do_repeat_click(self, button_index=0):
        # Returns T/F to indicate if a repeat click should be performed (on mouse hold-down)
        # uses repeat_timer (as a timesheet) and held_timer (tick counter) to determine how
        # auto-clicks should work when button pressed down

        if self.repeat_timer is None:
            return False
        else:
            timer_store = self.held_timer[button_index]

            for i in range(-1, len(self.repeat_timer)):
                if i == len(self.repeat_timer) - 1:
                    break
                elif timer_store >= self.repeat_timer[i+1][0]:
                    timer_store -= self.repeat_timer[i+1][0]
                else:
                    break

            if 0 <= i < len(self.repeat_timer):
                return (timer_store % self.repeat_timer[i][1]) == 0

    def button_logic(self):
        # Check if button has been interacted with via mouse
        if self.mouse_collision():
            click_funcs = [self.leftclick, self.middleclick, self.rightclick]
            for mouse_button_index in range(3):
                # loop through each mouse button
                if self.new_pressed[mouse_button_index]:
                    self.held_timer[mouse_button_index] += 1

                    if self.old_pressed[mouse_button_index]:
                        # Pressed last time: check holding logic
                        if self.do_repeat_click(mouse_button_index):
                            click_funcs[mouse_button_index]()
                    else:
                        # New press: run function
                        click_funcs[mouse_button_index]()
                else:
                    # Not pressed => reset held timer
                    self.held_timer[mouse_button_index] = 0

    def get_rect(self):
        return None


class ImageInteractable(Interactable):
    # Template for interactable element that uses an image surface
    # instead of rectangles.
    def __init__(self,
                 sprite_list={},
                 **kwds):
        # Pass generic arguments up to Interactable.__init__()
        super().__init__(**kwds)

        # Store sprite list. For implementation of base ImageInteractable,
        # a key of 'DEFAULT' should be linked to single image you want to display
        self.sprite_list = sprite_list      # List of sprites to pull from for an image
        self.display_image = None           # Current image being displayed

    def get_image(self):
        # Returns an image surface to be drawn (blitted) onto a parent surface
        try:
            return self.sprite_list['DEFAULT']
        except KeyError:
            print("No DEFAULT key passed to sprite_list")

    def draw(self, to_screen=None):
        # Draws image to the described screen (based on get_image() and stored position (pos_x, pos_y)
        image_to_display = self.get_image()
        # Only perform draw if image has changed
        if image_to_display != self.display_image:
            # Scale image to current calculated size
            to_screen.blit(
                pygame.transform.scale(image_to_display, (self.width, self.height)), (self.pos_x, self.pos_y)
            )
            self.display_image = image_to_display

    def mouse_collision(self):
        # Custom logic for checking collision with an image-surface element
        # Because I don't know how to do it automatically with pygame, I'm coding it myself
        mouse_x, mouse_y = self.mouse_pos
        return (
            self.pos_x < mouse_x < self.pos_x + self.width
            and self.pos_y < mouse_y < self.pos_y + self.height
        )


class MineSweeperFace(ImageInteractable):
    def __init__(self,
                 object_link=None,
                 **kwds):
        super().__init__(**kwds)
        self.mine_field = object_link       # Link smiley to minefield

    def button_logic(self):
        # Simpler button logic for face:
        # (only left & right clicks, no hold-down)
        if self.mouse_collision():
            if not self.new_pressed[0] and self.old_pressed[0]:
                # Logic only on button release
                self.leftclick()
            elif not self.new_pressed[2] and self.old_pressed[2]:
                self.rightclick()

    def get_image(self):
        # Change expression on face based on game status
        #   Game ongoing - Regular smile
        #   Game won - Sunglasses
        #   Game loss - Xs on eyes
        #   Button Held - Held-down smile
        assert isinstance(self.mine_field, MineField)
        if self.mouse_collision() and self.new_pressed[0]:
            image_key = "HAPPY_PRESSED"
        elif self.mouse_collision() and self.new_pressed[2]:
            image_key = "SURPRISED"
        else:
            if self.mine_field.game_state() < 0:
                image_key = 'DEAD'
            elif self.mine_field.game_state() > 0:
                image_key = 'COOL'
            else:
                image_key = 'HAPPY'

        return self.sprite_list[image_key]


class MineSweeperGrid:
    # Big daddy grid manager. Controls which of the MineSweeperSquares get drawn and which don't
    def __init__(self, pos_x, pos_y,
                 tile_size, sprite_list,
                 object_link: MineField):

        self.sprite_list = sprite_list
        self.mine_field = object_link
        self.tile_size = tile_size
        self.pos = (pos_x, pos_y)
        self.do_redraw = True  # Flag indicating if entire field should be redrawn
        self.mouse_pos = (-1, -1)
        self.squares = {
            'NEW': None,
            'OLD': None
        }
        self.pressed = {
            'NEW': (False, False, False),
            'OLD': (False, False, False)
        }

    def flag_redraw(self):
        self.do_redraw = True

    def draw(self, to_screen):
        if self.do_redraw:
            # Loop through every tile and redraw
            for tile_list in self.mine_field.field:
                for tile_to_draw in tile_list:
                    self.draw_tile(to_screen, tile_to_draw)
            self.do_redraw = False
        else:
            # Redraw only the currently & recently interacted-with tiles
            for tile_items in self.squares.items():
                tile_to_draw = tile_items[1]
                if tile_to_draw is not None:
                    self.draw_tile(to_screen, tile_to_draw)

    def draw_tile(self, to_screen, field_square):
        assert isinstance(field_square, FieldSquare)
        grid_x, grid_y = field_square.pos # Relative x,y position in grid of buttons
        pos_x, pos_y = self.pos # x,y position of Grid structure on main screen

        image_to_draw = self.get_image(field_square)
        draw_x = pos_x + grid_x * self.tile_size
        draw_y = pos_y + grid_y * self.tile_size

        to_screen.blit(
            pygame.transform.scale(image_to_draw,(self.tile_size, self.tile_size)),
            (draw_x, draw_y)
        )

    def get_image(self, field_square):
        if field_square.mine_removed:
            image_key = "mineRemoved"
        elif field_square.is_revealed:
            if field_square.has_mine:
                # All below are only visible on game over (revealed mine)
                if field_square.source_explosion:
                    image_key = "mineClicked"
                else:
                    image_key = "mine"
            else:
                # revealed, no mine
                if field_square.has_flag:
                    # This should also only be visible on a gameover
                    image_key = 'mineFalse'
                elif field_square.neighboring_mines == 0:
                    image_key = "empty"
                else:
                    # No flag & >0 neighbors
                    image_key = "grid{}".format(field_square.neighboring_mines)
        else:
            # not revealed
            if field_square.has_flag:
                image_key = "flag"
            elif self.pressed['NEW'][0] and field_square.pos == self.map_coords(self.mouse_pos):
                # Have to include mouse_collision to check if a specific button is pressed
                image_key = "empty"
            else:
                image_key = "grid"

        return self.sprite_list[image_key]

    def store_inputs(self, mouse_pos=(-1, -1), mouse_buttons=(False, False, False)):
        self.mouse_pos = mouse_pos
        tile_x, tile_y = self.map_coords(mouse_pos)

        self.squares['OLD'] = self.squares['NEW']
        self.squares['NEW'] = self.mine_field.get_square(tile_x, tile_y)

        self.pressed['OLD'] = self.pressed['NEW']
        self.pressed['NEW'] = mouse_buttons

    def map_coords(self, mouse_pos):
        mouse_x, mouse_y = mouse_pos
        pos_x, pos_y = self.pos

        rel_x = mouse_x - pos_x
        rel_y = mouse_y - pos_y

        tile_x = math.floor(rel_x / self.tile_size)
        tile_y = math.floor(rel_y / self.tile_size)
        if (
                0 <= tile_x < self.mine_field.size[0]
                and 0 <= tile_y < self.mine_field.size[1]
        ):
                return (tile_x, tile_y)
        else:
            return -1, -1

    def button_logic(self):
        # Leftmouse: pressed and let go
        if not self.pressed['NEW'][0] and self.pressed['OLD'][0]:
            self.leftclick()
        # Rightmouse: click
        elif self.pressed['NEW'][2] and not self.pressed['OLD'][2]:
            self.rightclick()

    def leftclick(self):
        # Executes dig on tile, if it exists in this grid
        try:
            coord_x, coord_y = self.map_coords(self.mouse_pos)
            self.mine_field.dig(coord_x, coord_y)
            self.flag_redraw()
        except TypeError:
            pass

    def rightclick(self):
        # Executes flag on tile, if it exists in this grid
        try:
            coord_x, coord_y = self.map_coords(self.mouse_pos)
            self.mine_field.toggle_flag(coord_x, coord_y)
        except TypeError:
            pass


class Button(Interactable):
    # A type of interactable drawn using
    # pygame rectangles & text surfaces
    def __init__(self,
                 colormap=None, do_mouseover_color=True,
                 box_text="",
                 text_font='Arial',
                 font_size=10,
                 leftclick=None, rightclick=None,
                 textfunc=None, colorfunc=None,
                 **kwds):
        super().__init__(**kwds)

        self.rect = pygame.rect.Rect(self.pos_x, self.pos_y, self.width, self.height)

        self.display_color = None                       # Stores text currently drawn on button
        self.display_text = None                        # Stores text currently drawn on button
        self.do_mouseover_color = do_mouseover_color    # Flag for shifting color on mouseover

        # DEFAULTS:
        # Values to use for base-class Buttons
        # These act as defaults for button sub-types

        self.default_shape_color = {            # Default colors if none other specified
            'BASE': (255, 255, 255),
            'MOUSEOVER': (200, 200, 200)
        }

        # Support partial dictionaries to define color defaults
        # Only interact types provided in dictionary will be updated.
        # The rest will be set to default values
        for itype in self.default_shape_color:
            try:
                self.default_shape_color[itype] = colormap[itype]
            except KeyError:
                # nonexistant key: pass
                pass
            except TypeError:
                # Type is None: also pass
                pass

        self.default_text = box_text            # Default text to use if none other specified
        self.default_font = text_font           # Default font if none other specified
        self.default_font_size = font_size      # Default font size if none other specified

        # Render initial text objects/details
        self.text_surface = pygame.font.SysFont(text_font, font_size).render(box_text, True, (0, 0, 0))
        self.text_rect = self.text_surface.get_rect(center=self.rect.center)

        self.mouse_pos = (-1, -1)
        self.mouse_buttons = (False, False, False)

        # Base Button class uses methods defined
        # on initialization for onclick methods
        self.default_leftclick = leftclick
        self.default_rightclick = rightclick
        self.default_textfunc = textfunc
        self.default_colorfunc = colorfunc

    def get_rect(self):
        return self.rect

    def get_color(self):
        # Method that retrieves the color a button should be at time of call
        if self.default_colorfunc is None:
            if self.rect.collidepoint(self.mouse_pos) and self.do_mouseover_color:
                return self.default_shape_color['MOUSEOVER']
            else:
                return self.default_shape_color['BASE']
        else:
            return self.default_colorfunc()

    def get_text(self):
        # Method that returns the text a button should show at time of call
        if self.default_textfunc is None:
            return self.default_text
        else:
            return self.default_textfunc()

    def change_text(self, new_text="", new_font='Arial', new_font_size=10):
        # Change the text of button by redefining default_text, text surface & text object
        self.text_surface = pygame.font.SysFont(new_font, new_font_size).render(new_text, True, (0, 0, 0))
        self.text_rect = self.text_surface.get_rect(center=self.rect.center)
        self.default_text = new_text

    def draw(self, to_screen, force=False):
        # Draw button color & text

        # Handle None to prevent parachute error
        if to_screen is None:
            print("Warning: Screen passed to button for drawing is None")
            return

        text_to_draw = self.get_text()
        color_to_draw = self.get_color()

        do_change_text = (text_to_draw != self.display_text) or force
        do_draw_rect = (color_to_draw != self.display_color) or force

        # First, rerender text objects if text has changed
        if do_change_text:
            self.change_text(new_text=text_to_draw)

        # Then, draw in button rectangle (if anything has changed)
        # If either changes (text or color) we have to draw both
        # - Redrawing rectangle covers up old text, then we have to
        #   redraw text on top
        if do_draw_rect or do_change_text:
            try:
                pygame.draw.rect(to_screen, color_to_draw, self.rect)
            except:
                print("HERE")
            to_screen.blit(self.text_surface, self.text_rect)
            self.display_color = color_to_draw
            self.display_text = text_to_draw


class ObjectButton(Button):
    # Specialized button whose color and text elements
    # are dependent on a linked object's get_color() and get_text() methods
    def __init__(self, object_link, **kwds):
        self.object = object_link
        super().__init__(**kwds)

    def get_color(self):
        # "Try"-ing to return that result ends up returning "None" anyway
        # so I save the result in to_return, then use super() if that fails
        try:
            to_return = self.object.get_color()
        except AttributeError:
            to_return = super().get_color()
        return to_return

    def get_text(self):
        try:
            return self.object.get_text()
        except AttributeError:
            return self.default_text


class GameSettingButton(ObjectButton):
    # ObjectButton that grabs text from the provided game setting type
    # (mine_count, row_count, or column_count) to write as text
    def __init__(self, setting_type, **kwds):
        self.setting_type = setting_type
        super().__init__(**kwds)

    def get_text(self):
        return str(self.object.settings[self.setting_type])


class FullScreenButton(ObjectButton):
    def get_text(self):
        if self.object.settings['fullscreen']:
            return "FULLSCREEN"
        else:
            return "NO FULLSCREEN"

    def get_color(self):

        if self.object.settings['fullscreen']:
            to_return = (0, 255, 0)
        else:
            to_return = (255, 0, 0)
        if self.rect.collidepoint(self.mouse_pos) and self.do_mouseover_color:
                to_return = tuple([col * 0.8 for col in to_return])
        return to_return


### NON-INTERACTABLES ###

class DigitDisplay:
    def __init__(self,
                 pos_x=0, pos_y=0,
                 digit_width=-1, digit_height=-1,
                 num_digits=1,
                 sprite_list={'DEFAULT': pygame.Surface((1, 1))}
                 ):

        self.pos = (pos_x, pos_y)
        self.sprite_list = sprite_list          # reference of sprites to be used for digits.
        self.num_digits = max(1, num_digits)    # number of digit slots to hold. Must be at least one
        self.current_number = None              # Current number being shown by DigitDisplay

        # Set dimensions of digit to those of the first digit
        # Given in sprite_list (if none or invalid ones are provided)
        if digit_width > 0:
            self.digit_width = digit_width
        else:
            self.digit_width = list(sprite_list.items())[0][1].get_width()

        if digit_height > 0:
            self.digit_height = digit_height
        else:
            self.digit_height = list(sprite_list.items())[0][1].get_height()

    def force_draw(self, to_screen, image_key_list):
        # Forcefully update display based on a list of image keys
        # no autocalculation for a number is done
        digits_drawn = 0
        for sprite_key in image_key_list:
            to_screen.blit(
                pygame.transform.scale(self.sprite_list[sprite_key], (self.digit_width, self.digit_height)),
                (self.pos[0] + self.digit_width * digits_drawn, self.pos[1])
            )
            digits_drawn += 1

    def draw(self, to_screen, number):
        digits_to_draw = self.get_digits(number)
        num_blanks = self.num_digits - len(digits_to_draw)

        digits_drawn = 0
        for nb in range(num_blanks):
            to_screen.blit(
                pygame.transform.scale(self.sprite_list['blank'], (self.digit_width, self.digit_height)),
                (self.pos[0] + self.digit_width * digits_drawn, self.pos[1])
            )
            digits_drawn += 1

        for sprite_key in digits_to_draw:
            to_screen.blit(
                pygame.transform.scale(self.sprite_list[sprite_key], (self.digit_width, self.digit_height)),
                (self.pos[0] + self.digit_width * digits_drawn, self.pos[1])
            )
            digits_drawn += 1

    def get_digits(self, num):
        # Takes an integer and reduces it to a list of its digits

        if num < 0:
            # Set variables to handle negative sign
            if self.num_digits == 1:
                # Special case exception: one-digit counters have no room for negatives
                return ["0"]
            else:
                # Technically this doesn't need to be an else block, but I think the code looks nicer this way
                digits = ["dash"]
                exponent_offset = 1
                num = abs(num)
        elif num == 0:
            # Return 0 immediately - the math used further on to determine digits doesn't like 0s
            return ["0"]
        else:
            # Base setup
            digits = []
            exponent_offset = 0

        # Numbers of too many digits are reduced to the maximum number for available digits
        num = min(num, 10**(self.num_digits - exponent_offset) - 1)
        try:
            num_digits = 1 + int(math.log10(num))
        except:
            print("huh?")

        for digit_index in range(num_digits):
            # 10^x number representing current digit (left to right)
            # e.g. tens place is 10, 100s place is 100, etc.
            current_factor = 10 ** (num_digits - (digit_index + 1))
            # divide by current factor and use int to chop off remainder for result
            to_append = int(num/current_factor)
            digits.append(str(to_append))
            # use current factor to chop off considered digit for next iteration
            num -= to_append * current_factor
        return digits

