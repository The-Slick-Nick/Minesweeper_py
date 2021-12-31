from Interface import *
from GameVariables import *
from math import ceil
import os
import sys
import time
import pygame
import matplotlib
pygame.init()


class GameInstance:
    def __init__(self):
        self.current_screen = None
        self.show_startmenu = False
        self.show_game = False

        self.clock = pygame.time.Clock()

        self.screen_control = {
            'STARTMENU': False,
            'GAME': False,
            'RESTART': False,
            'CONFIG': False,
            'GAMEOVER': False
        }

        # Directly user-controlled settings
        self.settings = {
            'mine_count': 15,         # Minimum 1    Maximum: (rows * columns) / 2
            'row_count': 10,          # Minimum 1    Maximum: 100
            'column_count': 10,       # Minimum 4    Maximum: 100
            'fullscreen': False,      # Controls if game will open in fullscreen mode
            'screen_size': 500        # Maximum dimension (width or height) of non-fullscreen screen,
        }

        # Display settings calculated based on existing settings
        self.display_settings = {
            'menu_bar_height': 50,   # Height of the bit at the top with the counters & the face
            'face_size': 32.0,       # Size of the face button
            'screen_width': 500,     # Current calculated width for screen
            'screen_height': 500,    # Current calculated height for screen
            'box_size': 32.0         # Current calculated size of the minesweeper squares
        }

        self.menu_elements = {}      # images for drawing menu elements
        self.face_sprites = {}       # sprites of the minesweeper dude's faces
        self.grid_sprites = {}       # sprite of grid tile icons
        self.digit_sprites = {}      # sprites of digital-clock style digits
        self.load_images()           # populate sprite_lists described above

        self.screen_resolution = (pygame.display.Info().current_w, pygame.display.Info().current_h)

        print("Resolution: {}".format(pygame.display.Info()))

        self.run_startmenu()

    def load_images(self):
        self.menu_elements['MENU_BAR'] = pygame.image.load(os.path.join("Minesweeper_py", "Resources", "MenuElements", "menubar.png"))

        # For each file in Sprites folder, add its filename as a
        # reference to the loaded image in a dictionary
        # e.g. 'grid3.png' -> self.sprite_list['grid3'] = grid3.png
        for image_name in os.listdir(
            os.path.join(os.getcwd(), "Minesweeper_py", "Resources", "Sprites", "Grid")
        ):
            self.grid_sprites[
                image_name[:-4]
            ] = pygame.image.load(os.path.join("Minesweeper_py", "Resources", "Sprites", "Grid", image_name))

        # Load faces the same way
        for image_name in os.listdir(
            os.path.join(os.getcwd(),"Minesweeper_py", "Resources", "Sprites", "Faces")
        ):
            self.face_sprites[
                image_name[:-4]
            ] = pygame.image.load(os.path.join("Minesweeper_py", "Resources", "Sprites", "Faces", image_name))

        # Load digits the same say
        for image_name in os.listdir(
            os.path.join(os.getcwd(),"Minesweeper_py", "Resources", "Sprites", "Digits")
        ):
            self.digit_sprites[
                image_name[:-4]
            ] = pygame.image.load(os.path.join("Minesweeper_py", "Resources", "Sprites", "Digits", image_name))

    def exit_screen(self, screen_type):
        # Marks a described loop control flag as False (to end that loop)
        self.screen_control[screen_type] = False

    def toggle_fullscreen(self):
        self.settings['fullscreen'] = not self.settings['fullscreen']

        # call setting adjustment to trigger auto-correction of settings
        # (to minimums & maximums)
        self.adjust_settings('screen_size', 0)

    def adjust_settings(self, setting_type, adjust_amount):
        # Change game settings (rows, columns, number of mines)
        # Then auto-correct those settings based on set minimums/maximums
        self.settings[setting_type] += adjust_amount

        self.settings['screen_size'] = max(
            200,
            min(
                min(self.screen_resolution[0], self.screen_resolution[1]),
                self.settings['screen_size']
            )
        )

        min_rows = 1
        if self.settings['fullscreen']:
            max_rows = int(self.screen_resolution[1]/10)
            max_columns = int(self.screen_resolution[0]/10)
        else:
            max_rows = int(self.settings['screen_size']/10)
            max_columns = max_rows

        self.settings['row_count'] = min(
            max(min_rows, self.settings['row_count']),
            max_rows
        )

        # Work around minimum screen width of 120:
        # Based on projected square size, we must have enough columns (at that size) to get size 120 or greater
        # num_columns * square_size >= 120
        min_columns = max(1, ceil(120 * (self.settings['row_count'] / self.settings['screen_size'])))


        # min_columns < column_count < max_columns
        self.settings['column_count'] = min(
            max(min_columns, self.settings['column_count']),
            max_columns
        )

        # 1 < num_mines < grid_size/2
        self.settings['mine_count'] = min(
            max(1, self.settings['mine_count']),
            int((self.settings['row_count'] * self.settings['column_count']) / 2)
        )

    @staticmethod
    def screen_is_dead(test_screen):
        # Returns a T/F value indicating if provided screen is dead
        # By attempting to access size property
        try:
            test_screen.get_size()
            return_val = False
        except pygame.error:
            return_val = True

        return return_val

    def run_startmenu(self):
        screen_height = 300
        screen_width = 300

        # buttons on main menu
        menu_buttons = [
            # START BUTTON: Starts game
            Button(
                pos_x=0,
                pos_y=0,
                height=screen_height/3,
                width=screen_width,
                colormap={'BASE': (10, 150, 150), 'MOUSEOVER': (5, 100, 100)},
                box_text="START",
                leftclick=self.run_game
            ),
            # CONFIG BUTTON: Opens config menu
            Button(
                pos_x=0, pos_y=screen_height/3,
                height=screen_height/3,
                width=screen_width,
                box_text="CONFIG",
                leftclick=self.run_settings
            ),
            # EXIT BUTTON: Exits Main Menu
            Button(
                pos_x=0,
                pos_y=2 * screen_height/3,
                height=screen_height/3,
                width=screen_width,
                colormap={'BASE': (200, 0, 0), 'MOUSEOVER': (100, 0, 0)},
                box_text='EXIT',
                leftclick=lambda: self.exit_screen("STARTMENU")
            )
        ]

        menu_screen = pygame.display.set_mode([screen_width, screen_height])

        pygame.display.set_caption("Minesweeper - Menu")

        self.screen_control['STARTMENU'] = True
        while self.screen_control['STARTMENU']:
            ### RESOLVE USER INPUT ###

            for ev in pygame.event.get():
                if ev.type == pygame.QUIT or ev.type == pygame.KEYDOWN and ev.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()

            # Store mouse status (position & buttons) to each button
            for mb_inputs in menu_buttons:
                mb_inputs.store_inputs(pygame.mouse.get_pos(), pygame.mouse.get_pressed(3))

            ### UPDATE GAME VARIABLES ###

            # Check each button for clicked or not, run logic
            for mb_logic in menu_buttons:
                mb_logic.button_logic()

            ### UPDATE DISPLAY ###

            # Re-establish screen if it is dead
            if self.screen_is_dead(menu_screen):
                menu_screen = pygame.display.set_mode([screen_width, screen_height])
                pygame.display.set_caption("Minesweeper - Menu")

            # Draw each button
            for mb_display in menu_buttons:
                mb_display.draw(menu_screen, force=True)

            pygame.display.flip()

    def run_settings(self):
        pygame.display.quit()
        pygame.display.init()

        screen_height = 200
        screen_width = 500

        self.screen_control['SETTINGS'] = True

        button_width = screen_width/5
        button_height = screen_height/4

        color_scheme = matplotlib.cm.get_cmap("Pastel2")
        def get_colormap(scale_factor):
            # Take a matplotlib colormap and convert it to
            # a colormap reference (dictionary of BASE vs MOUSEOVER rgb tuples) for use
            # in my buttons
            raw_cmap = color_scheme(scale_factor)
            base_color = tuple([col * 255 for col in raw_cmap[0:3]])
            mouseover_color = tuple([0.8 * col for col in base_color])
            return {'BASE': base_color, 'MOUSEOVER': mouseover_color}

        col_color = {
            'MINES': get_colormap(0.2),
            'NROW': get_colormap(0.4),
            'NCOL': get_colormap(0.6),
            'SCREEN': get_colormap(0.8)
        }

        # y-coordinates for element positioning
        row_y = {
            'LABEL': 0,
            'ADJUST': button_height/2,
            'NUM': 2 * screen_height/4,
            'CONFIRM': 3 * screen_height/4
        }
        # x-coordinates for element positioning
        column_x = {
            'MINES': 0,
            'NROW': screen_width/5,
            'NCOL': 2 * screen_width/5,
            'SCREEN': 3 * screen_width/5,
            'FULLSCREEN': 4 * screen_width/5
        }
        # standard time-sheet for button hold-down (on adjustment buttons)
        adjustment_timer = [
            (0, 10),
            (60, 5),
            (120, 1)
        ]

        config_buttons = [
            ### LABEL ROW ###
            Button(
                pos_x=column_x['MINES'], pos_y=row_y['LABEL'],
                width=button_width, height=(1/2) * button_height,
                box_text='Mines', colormap=col_color['MINES'],
                do_mouseover_color=False
            ),
            Button(
                pos_x=column_x['NROW'], pos_y=row_y['LABEL'],
                width=button_width, height=(1/2) * button_height,
                box_text='Rows', colormap=col_color['NROW'],
                do_mouseover_color=False
            ),
            Button(
                pos_x=column_x['NCOL'], pos_y=row_y['LABEL'],
                width=button_width, height=(1/2) * button_height,
                box_text='Columns', colormap=col_color['NCOL'],
                do_mouseover_color=False
            ),
            Button(
                pos_x=column_x['SCREEN'], pos_y=row_y['LABEL'],
                width=button_width, height=(1/2) * button_height,
                box_text='Screen Size', colormap=col_color['SCREEN'],
                do_mouseover_color=False
            ),
            ### ADJUSTMENT ROW ###
            Button(
                pos_x=column_x['MINES'], pos_y=row_y['ADJUST'],
                width=button_width, height=(3/2) * button_height,
                box_text="+ -", colormap=col_color['MINES'],
                leftclick=lambda: self.adjust_settings('mine_count', 1),
                rightclick=lambda: self.adjust_settings('mine_count', -1),
                repeat_timer=adjustment_timer
            ),
            Button(
                pos_x=column_x['NROW'], pos_y=row_y['ADJUST'],
                width=button_width, height=(3/2) * button_height,
                box_text="+ -", colormap=col_color['NROW'],
                leftclick=lambda: self.adjust_settings('row_count', 1),
                rightclick=lambda: self.adjust_settings('row_count', -1),
                repeat_timer=adjustment_timer
            ),
            Button(
                pos_x=column_x['NCOL'], pos_y=row_y['ADJUST'],
                width=button_width, height=(3/2) * button_height,
                box_text="+ -", colormap=col_color['NCOL'],
                leftclick=lambda: self.adjust_settings('column_count', 1),
                rightclick=lambda: self.adjust_settings('column_count', -1),
                repeat_timer=adjustment_timer
            ),
            Button(
                pos_x=column_x['SCREEN'], pos_y=row_y['ADJUST'],
                width=button_width, height=(3/2) * button_height,
                box_text="+ -", colormap=col_color['SCREEN'],
                leftclick=lambda: self.adjust_settings('screen_size', 10),
                rightclick=lambda: self.adjust_settings('screen_size', -5),
                repeat_timer=adjustment_timer
            ),
            FullScreenButton(
                object_link=self,
                pos_x=column_x['FULLSCREEN'], pos_y=0,
                width=button_width, height=3 * button_height,
                leftclick=lambda: self.toggle_fullscreen(),
                repeat_timer=adjustment_timer
            ),
            ### NUMBER DISPLAY ROW ###
            GameSettingButton(
                object_link=self, setting_type='mine_count',
                pos_x=column_x['MINES'], pos_y=row_y['NUM'],
                colormap=col_color['MINES'], do_mouseover_color=False,
                width=button_width, height=button_height
            ),
            GameSettingButton(
                object_link=self, setting_type='row_count',
                pos_x=column_x['NROW'], pos_y=row_y['NUM'],
                colormap=col_color['NROW'], do_mouseover_color=False,
                width=button_width, height=button_height
            ),
            GameSettingButton(
                object_link=self, setting_type='column_count',
                pos_x=column_x['NCOL'], pos_y=row_y['NUM'],
                colormap=col_color['NCOL'], do_mouseover_color=False,
                width=button_width, height=button_height
            ),
            GameSettingButton(
                object_link=self, setting_type='screen_size',
                pos_x=column_x['SCREEN'], pos_y=row_y['NUM'],
                colormap=col_color['SCREEN'], do_mouseover_color=False,
                width=button_width, height=button_height
            ),
            ### CONFIRM BUTTON ###
            Button(
                pos_y=row_y['CONFIRM'], pos_x=0,
                width=screen_width, height=button_height,
                colormap=get_colormap(1),
                box_text='CONFIRM', leftclick=lambda: self.exit_screen('SETTINGS')
            )
        ]

        config_screen = pygame.display.set_mode([screen_width, screen_height])
        pygame.display.set_caption("Game Settings")

        # Menu screen loop
        while self.screen_control['SETTINGS']:
            self.clock.tick(60)

            ### PROCESS USER INPUT ###
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    pygame.quit()

            for cb in config_buttons:
                cb.store_inputs(pygame.mouse.get_pos(), pygame.mouse.get_pressed(3))

            ### UPDATE GAME VARIABLES ###
            for cb in config_buttons:
                cb.button_logic()

            ### UPDATE DISPLAY ###
            if self.screen_is_dead(config_screen):
                config_screen = pygame.display.set_mode([screen_width, screen_height])
                pygame.display.set_caption("Game Settings")

            for cb in config_buttons:
                cb.draw(config_screen)

            pygame.display.flip()

        pygame.display.quit()
        pygame.display.init()

    def set_display_settings(self):
        """

        :rtype: pygame.Surface
        """
        # Static values
        menu_bar_height = 75

        self.display_settings['menu_bar_height'] = menu_bar_height
        self.display_settings['face_size'] = (menu_bar_height/2)

        if self.settings['fullscreen']:
            screen_width, screen_height = self.screen_resolution
            box_size = 0.95 * min(
                screen_height/self.settings['row_count'],
                screen_width/self.settings['column_count']
            )
        else:
            box_size = 0.95 * min(
                self.settings['screen_size']/self.settings['row_count'],
                self.settings['screen_size']/self.settings['column_count']
            )
            screen_width = box_size * self.settings['column_count']
            screen_height = box_size * self.settings['row_count']

        self.display_settings['screen_width'] = screen_width
        self.display_settings['screen_height'] = screen_height
        self.display_settings['box_size'] = box_size

        if self.settings['fullscreen']:
            # Though display_settings aren't used for setting up screen,
            # if fullscreen is selected, we'll still need those attributes
            # to determine display element sizes
            return pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            return pygame.display.set_mode([screen_width, screen_height + menu_bar_height])

    def run_game(self):
        # Potential new screen size for game: close and reopen
        # (Things appear off-center sometimes if I don't do this, idk)
        pygame.display.quit()
        pygame.display.init()

        game_screen = self.set_display_settings()

        # Create minefield from game settings
        mine_field = MineField(self.settings['column_count'], self.settings['row_count'])

        # Add mines to minefield from game settings
        mine_field.populate_mines(self.settings['mine_count'])

        # Button functions (that require >1 line)
        def exit_all():
            self.exit_screen("GAME")
            self.exit_screen("RESTART")

        def reset_mines():
            # Resets mine field mines AND restarts game loop
            mine_field.reset(self.settings['mine_count'])
            game_grid.flag_redraw()
            self.exit_screen("GAME")

        def commit_mines():
            mine_field.commit_mines()
            game_grid.flag_redraw()

        # Create buttons
        menu_buttons = [
            # FACE BUTTON
            MineSweeperFace(
                # Center in menu bar
                pos_x=(self.display_settings['screen_width'] / 2) - (self.display_settings['face_size'] / 2),
                pos_y=(self.display_settings['menu_bar_height'] / 2) - (self.display_settings['face_size'] / 2),
                width=self.display_settings['face_size'], height=self.display_settings['face_size'],
                leftclick=reset_mines, rightclick=commit_mines,
                object_link=mine_field,
                sprite_list=self.face_sprites
            )
        ]
        game_grid = MineSweeperGrid(
            pos_x=(self.display_settings['screen_width']/2) - (mine_field.size[0] * self.display_settings['box_size']/2),
            pos_y=self.display_settings['menu_bar_height'],
            tile_size=self.display_settings['box_size'],
            sprite_list=self.grid_sprites,
            object_link=mine_field
        )

        # Use the blank digit sprite as a template for digit sprite sizes
        digit_size_ratio = self.digit_sprites['blank'].get_width()/self.digit_sprites['blank'].get_height()
        d_height = self.display_settings['face_size'] * 0.9
        d_width = digit_size_ratio * d_height

        # Create digit-style counters
        mine_counter = DigitDisplay(
                sprite_list=self.digit_sprites,
                digit_height=d_height, digit_width=d_width,
                num_digits=3,
                pos_x=(39/40) * self.display_settings['screen_width'] - (3 * d_width),
                pos_y=(1/2) * self.display_settings['menu_bar_height'] - (1/2) * d_height
            )
        time_counter = DigitDisplay(
                sprite_list=self.digit_sprites,
                digit_height=d_height, digit_width=d_width,
                num_digits=3,
                pos_x=(1/40) * self.display_settings['screen_width'],
                pos_y=(1/2) * self.display_settings['menu_bar_height'] - (1/2) * d_height
        )

        # Fill background with grey and draw menu bar texture at top
        game_screen.fill((192, 192, 192))
        game_screen.blit(pygame.transform.scale(
            self.menu_elements['MENU_BAR'], (self.display_settings['screen_width'], self.display_settings['menu_bar_height'])),
            (0, 0)
        )
        pygame.display.set_caption("Minesweeper")

        self.screen_control['RESTART'] = True
        while self.screen_control['RESTART']:

            self.screen_control['GAME'] = True
            tick_count = 0 # Stores ticks since game start

            # Run main game loop
            while mine_field.game_state() == 0 and self.screen_control['GAME']:
                self.clock.tick(60)

                st = time.time()
                ### RESOLVE USER INPUT ###
                for ev in pygame.event.get():
                    if ev.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    elif ev.type == pygame.KEYDOWN:
                        if ev.key == pygame.K_ESCAPE:
                            exit_all()
                        elif ev.key == pygame.K_r:
                            reset_mines()

                # Store mouse inputs for each button
                for allb in menu_buttons: # + game_buttons:
                    allb.store_inputs(pygame.mouse.get_pos(), pygame.mouse.get_pressed(3))
                game_grid.store_inputs(pygame.mouse.get_pos(), pygame.mouse.get_pressed(3))

                ### UPDATE GAME VARIABLES ###
                # Run click logic (where applicable) to buttons
                for allb in menu_buttons: # + game_buttons:
                    allb.button_logic()
                game_grid.button_logic()

                ### UPDATE DISPLAY ###
                # Re-draw base display if dead
                if self.screen_is_dead(game_screen):
                    game_screen = self.set_display_settings()
                    game_screen.fill((192, 192, 192))
                    game_screen.blit(pygame.transform.scale(
                        self.menu_elements['MENU_BAR'],
                        (self.display_settings['screen_width'], self.display_settings['menu_bar_height'])),
                        (0, 0)
                    )
                    pygame.display.set_caption("Minesweeper")

                for allb in menu_buttons: # + game_buttons:
                    allb.draw(game_screen)
                game_grid.draw(game_screen)

                # Since there are only two digit-counters, I choose to
                # manually update them each loop (as opposed to looping through a list of them)
                mine_counter.draw(game_screen, len(mine_field.mine_squares) - len(mine_field.flag_squares))
                time_counter.draw(game_screen, int(tick_count/60))

                pygame.display.flip()

                tick_count += 1

            # Once game loop ends, do GAMEOVER loop
            while self.screen_control['GAME']:
                self.clock.tick()
                ### RESOLVE USER INPUT ###

                for ev in pygame.event.get():
                    if ev.type == pygame.QUIT:
                        pygame.quit()
                        sys.exit()
                    elif ev.type == pygame.KEYDOWN:
                        # Escape returns to startmenu
                        if ev.key == pygame.K_ESCAPE:
                            exit_all()
                        elif ev.key == pygame.K_r:
                            # R resets game
                            reset_mines()

                for mb in menu_buttons:
                    mb.store_inputs(pygame.mouse.get_pos(), pygame.mouse.get_pressed())

                ### RESOLVE LOOP VARIABLES ###
                for mb in menu_buttons:
                    mb.button_logic()

                ### UPDATE DISPLAY ###
                if self.screen_is_dead(game_screen):
                    game_screen = self.set_display_settings()

                for mb in menu_buttons:
                    mb.draw(game_screen)

                pygame.display.flip()

        pygame.display.quit()
        pygame.display.init()
