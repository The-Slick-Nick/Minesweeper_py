from Interface import *
from GameVariables import *
from math import ceil
import pygame, os, sys
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

        self.game_settings = {
            'mine_count': 5,         # Minimum 1    Maximum: (rows * columns) / 2
            'row_count': 10,         # Minimum 1    Maximum: 100
            'column_count': 10       # Minimum 4    Maximum: 100
        }

        self.menu_elements = {}     # images for drawing menu elements
        self.face_sprites = {}      # sprites of the minesweeper dude's faces
        self.grid_sprites = {}      # sprite of grid tile icons
        self.digit_sprites = {}     # sprites of digital-clock style digits
        self.load_images()          # populate sprite_lists described above

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

    def adjust_settings(self, setting_type, adjust_amount):
        # Change game settings (rows, columns, number of mines)
        # Then auto-correct those settings based on set minimums/maximums
        self.game_settings[setting_type] += adjust_amount

        # 1 < row_count < 100
        self.game_settings['row_count'] = min(
            max(1, self.game_settings['row_count']),
            100
        )

        # Work around minimum screen width of 120:
        # Based on projected square size, we must have enough columns (at that size) to get size 120 or greater
        # num_columns * square_size >= 120
        min_columns = max(1, ceil(120 * (self.game_settings['row_count']/500)))

        # min_columns < column_count < 100
        self.game_settings['column_count'] = min(
            max(min_columns, self.game_settings['column_count']),
            100
        )

        # 1 < num_mines < grid_size/2
        self.game_settings['mine_count'] = min(
            max(1, self.game_settings['mine_count']),
            int((self.game_settings['row_count'] * self.game_settings['column_count'])/2)
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
                leftclick=self.run_config
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

    def run_config(self):
        pygame.display.quit()
        pygame.display.init()

        screen_height = 400
        screen_width = 300

        self.screen_control['CONFIG'] = True

        row_y = {
            'LABEL': 0,
            'ADJUST': screen_height/4,
            'NUM': 2 * screen_height/4,
            'CONFIRM': 3 * screen_height/4
        }
        column_x = {
            'MINES': 0,
            'NROW': screen_width/3,
            'NCOL': 2 * screen_width/3,
        }
        button_width = screen_width/3
        button_height = screen_height/4

        config_buttons = [
            ### LABEL ROW ###
            Button(
                pos_x=column_x['MINES'], pos_y=row_y['LABEL'],
                width=button_width, height=button_height,
                box_text='Mines'
            ),
            Button(
                pos_x=column_x['NROW'], pos_y=row_y['LABEL'],
                width=button_width, height=button_height,
                box_text='Rows'
            ),
            Button(
                pos_x=column_x['NCOL'], pos_y=row_y['LABEL'],
                width=button_width, height=button_height,
                box_text='Columns'
            ),
            ### ADJUSTMENT ROW ###
            Button(
                pos_x=column_x['MINES'], pos_y=row_y['ADJUST'],
                width=button_width, height=button_height,
                box_text="+ -",
                leftclick=lambda: self.adjust_settings('mine_count', 1),
                rightclick=lambda: self.adjust_settings('mine_count', -1),
                repeat_timer=[(0, 15), (120, 5), (120, 1)]
            ),
            Button(
                pos_x=column_x['NROW'], pos_y=row_y['ADJUST'],
                width=button_width, height=button_height,
                box_text="+ -",
                leftclick=lambda: self.adjust_settings('row_count', 1),
                rightclick=lambda: self.adjust_settings('row_count', -1),
                repeat_timer=[(0, 15), (120, 5), (120, 1)]
            ),
            Button(
                pos_x=column_x['NCOL'], pos_y=row_y['ADJUST'],
                width=button_width, height=button_height,
                box_text="+ -",
                leftclick=lambda: self.adjust_settings('column_count', 1),
                rightclick=lambda: self.adjust_settings('column_count', -1),
                repeat_timer=[(0, 15), (120, 5), (120, 1)]
            ),
            ### NUMBER DISPLAY ROW ###
            GameSettingButton(
                object_link=self, setting_type='mine_count',
                pos_x=column_x['MINES'], pos_y=row_y['NUM'],
                width=button_width, height=button_height
            ),
            GameSettingButton(
                object_link=self, setting_type='row_count',
                pos_x=column_x['NROW'], pos_y=row_y['NUM'],
                width=button_width, height=button_height
            ),
            GameSettingButton(
                object_link=self, setting_type='column_count',
                pos_x=column_x['NCOL'], pos_y=row_y['NUM'],
                width=button_width, height=button_height
            ),
            ### CONFIRM BUTTON ###
            Button(
                pos_y=row_y['CONFIRM'], pos_x=0,
                width=screen_width, height=button_height,
                box_text='CONFIRM', leftclick=lambda: self.exit_screen('CONFIG')
            )
        ]

        config_screen = pygame.display.set_mode([screen_width, screen_height])
        pygame.display.set_caption("Config")
        while self.screen_control['CONFIG']:
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
                pygame.display.set_caption("Config")

            for cb in config_buttons:
                cb.draw(config_screen)

            pygame.display.flip()

        pygame.display.quit()
        pygame.display.init()

    def run_game(self):
        pygame.display.quit()
        pygame.display.init()

        # Determine screen & square size
        # based on game settings
        base_size = 500
        if self.game_settings['row_count'] >= self.game_settings['column_count']:
            screen_height = base_size
            box_size = int(base_size / self.game_settings['row_count'])
            screen_width = box_size * self.game_settings['column_count']
        else:
            screen_width = base_size
            box_size = (base_size / self.game_settings['column_count'])
            screen_height = box_size * self.game_settings['row_count']

        menu_bar_height = 50
        face_size = 32

        # Create minefield from game settings
        mine_field = MineField(self.game_settings['column_count'], self.game_settings['row_count'])

        # Add mines to minefield from game settings
        mine_field.populate_mines(self.game_settings['mine_count'])

        # Button functions (that require >1 line)
        def exit_all():
            self.exit_screen("GAME")
            self.exit_screen("RESTART")

        def reset_mines():
            # Resets mine field mines AND restarts game loop
            mine_field.reset()
            self.exit_screen("GAME")

        # Create buttons
        menu_buttons = [
            # FACE BUTTON
            MineSweeperFace(
                pos_x=(screen_width / 2) - (face_size / 2),         # Center in menu bar
                pos_y=(menu_bar_height / 2) - (face_size / 2),      # Center in menu bar
                width=face_size, height=face_size,
                leftclick=reset_mines, rightclick=mine_field.commit_mines,
                object_link=mine_field,
                sprite_list=self.face_sprites
            )
        ]
        game_buttons = [
            MineSweeperSquare(
                object_link=mine_field.get_square(x, y),
                sprite_list=self.grid_sprites,
                pos_x=x * box_size,
                pos_y=menu_bar_height + y * box_size,
                width=box_size,
                height=box_size,
            )
            for x in range(mine_field.size[0])
            for y in range(mine_field.size[1])
        ]

        # Use the blank digit sprite as a template for digit sprite sizes
        d_height = self.digit_sprites['blank'].get_height()
        d_width = self.digit_sprites['blank'].get_width()

        # Create digit-style counters
        mine_counter = DigitDisplay(
                sprite_list=self.digit_sprites,
                digit_height=d_height, digit_width=d_width,
                num_digits=3,
                pos_x=screen_width - (15 + (3 * d_width)),
                pos_y=(1/2) * menu_bar_height - (1/2) * d_height
            )
        time_counter = DigitDisplay(
                sprite_list=self.digit_sprites,
                digit_height=d_height, digit_width=d_width,
                num_digits=3,
                pos_x=15,
                pos_y=(1/2) * menu_bar_height - (1/2) * d_height
        )

        # Setup game screen and menu bar texture
        game_screen = pygame.display.set_mode([screen_width, menu_bar_height + screen_height])
        game_screen.fill((192, 192, 192))
        pygame.display.set_caption("Minesweeper")
        game_screen.blit(
            pygame.transform.scale(self.menu_elements['MENU_BAR'], (screen_width, menu_bar_height)),
            (0, 0)
        )

        self.screen_control['RESTART'] = True
        while self.screen_control['RESTART']:

            self.screen_control['GAME'] = True
            tick_count = 0 # Stores ticks since game start

            # Run main game loop
            while mine_field.game_state() == 0 and self.screen_control['GAME']:
                self.clock.tick(60)

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
                for allb in menu_buttons + game_buttons:
                    allb.store_inputs(pygame.mouse.get_pos(), pygame.mouse.get_pressed(3))

                ### UPDATE GAME VARIABLES ###
                # Run click logic (where applicable) to buttons
                for allb in menu_buttons + game_buttons:
                    allb.button_logic()

                ### UPDATE DISPLAY ###
                # Re-draw base display if dead
                if self.screen_is_dead(game_screen):
                    game_screen = pygame.display.set_mode([screen_width, screen_height])
                    game_screen.fill((192, 192, 192))
                    pygame.display.set_caption("Minesweeper")
                    game_screen.blit(pygame.transform.scale(
                        self.menu_elements['MENU_BAR'], (screen_width, menu_bar_height)),
                        (0, 0)
                    )

                for allb in menu_buttons + game_buttons:
                    allb.draw(game_screen)

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
                    game_screen = pygame.display.set_mode([screen_width, screen_height])

                for mb in menu_buttons:
                    mb.draw(game_screen)

                pygame.display.flip()

        pygame.display.quit()
        pygame.display.init()
