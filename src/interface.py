import os
from typing import Optional

import pygame
from pygame.math import Vector2

from src.pygame_options import screen
from src.style import colors, print_on_screen
from src.survivor import Survivor
from src.world import Watcher, Climate

WIDTH, HEIGHT = screen.get_size()

def show_winners_stats(surface: pygame.Surface, start_pos: Vector2, winner: Survivor):
    """
    Displaying the winner's statistics on the floating window.
    """
    line_spacing = 50
    font_size = 35

    stats = {
        "Audacity" : round(winner.audacity, 2),
        "Resilience" : round(winner.resilience, 2),
        "Nb of hits" : winner.nb_of_hits
    }

    x = start_pos.x
    y = start_pos.y
    for label, value in stats.items():
        print_on_screen(surface, Vector2(x, y), txt=f"{label} : {value}", font_size=font_size)
        y += line_spacing

def show_winner_window(winner: Survivor):
    """
    Floating window appears when only one Survivor is left alive, highlighting the winner and displaying information
    about him or her.
    """

    # -------------------------------------------------------------------
    #                           FLOATING WINDOW
    # -------------------------------------------------------------------
    # Floating window size
    floating_win_size_ratio = 1.2
    floating_win_width = WIDTH / floating_win_size_ratio
    floating_win_height = HEIGHT / floating_win_size_ratio

    # Floating window position
    win_x = (WIDTH - floating_win_width) // 2
    win_y = (HEIGHT - floating_win_height) // 2

    # Floating window creation
    floating_win = pygame.Surface((floating_win_width, floating_win_height))
    floating_win.fill(colors["INTERFACE"])

    # -------------------------------------------------------------------
    #                       FLOATING WINDOW SHADOW
    # -------------------------------------------------------------------
    # Shadow effect for floating window displayed under it

    shadow_surface = pygame.Surface(floating_win.get_size())
    shadow_surface.fill(colors["BLACK"])
    shadow_surface.set_alpha(80)

    shadow_x = win_x + 5
    shadow_y = win_y + 5

    # -------------------------------------------------------------------
    #                  SHOWCASE AND MOVE/DRAW THE WINNER
    # -------------------------------------------------------------------
    # In order, we need to :
    # - Create the showcase surface
    # - Move and draw the Survivor on it
    # - Display the surface on the floating window

    # Winner showcase
    showcase_edge = floating_win_width / 4
    showcase = pygame.Surface((showcase_edge, showcase_edge))
    showcase.fill(colors["SHOWCASE"])

    # Each frame the window is displayed, the Survivor's energy is reset to
    # maximum, giving it unlimited energy to strut his stuff in the showcase.
    winner.energy = winner.energy_default
    winner.move_on_showcase(showcase_edge)
    winner.show_on_showcase(showcase, showcase_edge)

    # Showcase placement
    x = (floating_win_width - showcase_edge) - 10
    y = 10

    # Draws showcase on the floating window
    floating_win.blit(showcase, (x, y))

    # -------------------------------------------------------------------
    #                           TEXTS DISPLAY
    # -------------------------------------------------------------------
    # All stat texts will be centered and aligned on the header's 'y' axis.
    header_pos = Vector2(floating_win_width/2.5, 50)
    start_pos = Vector2(header_pos.x, header_pos.y + 80)

    # Header
    print_on_screen(floating_win, header_pos, txt=f"WINNER : {winner.name}", font_size=50)

    # Stats display
    show_winners_stats(floating_win, start_pos, winner)

    # -------------------------------------------------------------------
    #                         SHOW EVERYTHING
    # -------------------------------------------------------------------
    screen.blit(shadow_surface, (shadow_x, shadow_y)) # Draws shadow on main screen
    screen.blit(floating_win, (win_x, win_y)) # Draws the floating window on main screen

class Hud:
    """

    """
    def __init__(self):
        # -------------------------------------------------------------------
        #                           SCREEN SIZE
        # -------------------------------------------------------------------
        self.screen_width = screen.width
        self.screen_height = screen.height

        # -------------------------------------------------------------------
        #                          CLIMATE SLOT
        # -------------------------------------------------------------------
        self.climate_slot_path: str = os.path.join("assets", 'hud', "climate_slot.png")
        self.climate_slot_image: pygame.Surface = pygame.image.load(self.climate_slot_path)
        self.climate_slot_image.set_alpha(150)

        self.climate_slot_pos: Vector2 = Vector2(0, 0)
        self.climate_slot_screen_ratio = 0.07
        self.climate_slot_offset = 10
        self.climate_slot_edge = self.climate_slot_image.get_size()[0]

        # -------------------------------------------------------------------
        #                         CLIMATE IMAGES
        # -------------------------------------------------------------------
        # Temperate image
        self.temperate_climate_path: str = os.path.join("assets", 'hud', "temperate.png")
        self.temperate_climate_image: pygame.Surface = pygame.image.load(self.temperate_climate_path)

        # Cold image
        self.cold_climate_path: str = os.path.join("assets", 'hud', "cold.png")
        self.cold_climate_image: pygame.Surface = pygame.image.load(self.cold_climate_path)

        # Hot image
        self.hot_climate_path: str = os.path.join("assets", 'hud', "hot.png")
        self.hot_climate_image: pygame.Surface = pygame.image.load(self.hot_climate_path)

        self.climate_image_pos: Vector2 = Vector2(0, 0)
        self.climate_image_slot_ratio = 0.9
        self.climate_image_size = 1
        self.current_climate_image: pygame.Surface = self.temperate_climate_image
        # -------------------------------------------------------------------
        #                              TEXT
        # -------------------------------------------------------------------
        # HUD texts
        self.txt_temperature_pos: Optional[Vector2] = None
        self.txt_survivors_alive_pos: Optional[Vector2] = None

        # -------------------------------------------------------------------
        #                             STATES
        # -------------------------------------------------------------------
        self.current_climate: Climate = Climate.TEMPERATE
        self.watcher: Optional[Watcher] = None

        # -------------------------------------------------------------------
        #                       SCALING & POSITIONING
        # -------------------------------------------------------------------
        self.scaling()
        self.positioning()

    def scaling(self):
        """
        Resizes HUD elements according to window size.
        """
        # Climate slot scaling
        self.climate_slot_edge = self.screen_width * self.climate_slot_screen_ratio
        self.climate_slot_image = pygame.transform.scale(self.climate_slot_image, (self.climate_slot_edge,
                                                                                   self.climate_slot_edge))

        # Climate images scaling value (only one side value since the images are square).
        self.climate_image_size = self.climate_slot_edge * self.climate_image_slot_ratio

        # Temperate image scaling
        self.temperate_climate_image = pygame.transform.scale(self.temperate_climate_image,
                                                              (self.climate_image_size,
                                                               self.climate_image_size))
        # Cold image scaling
        self.cold_climate_image = pygame.transform.scale(self.cold_climate_image,(self.climate_image_size,
                                                          self.climate_image_size))
        # Hot image scaling
        self.hot_climate_image = pygame.transform.scale(self.hot_climate_image, (self.climate_image_size,
                                                                                 self.climate_image_size))

    def positioning(self):
        """
        Positions HUD elements according to window size.
        """
        # -------------------------------------------------------------------
        #                     CLIMATE SLOT POSITIONING
        # -------------------------------------------------------------------
        # Placing the climate slot.
        slot_offset = self.climate_slot_offset
        self.climate_slot_pos = Vector2((self.screen_width - self.climate_slot_edge) - slot_offset, slot_offset)

        # -------------------------------------------------------------------
        #                    CLIMATE IMAGE POSITIONING
        # -------------------------------------------------------------------
        # Get slot center.
        slot_center_x = self.climate_slot_pos.x + (self.climate_slot_edge // 2)
        slot_center_y = self.climate_slot_pos.y + (self.climate_slot_edge // 2)

        # Places the image in the center of the slot.
        climate_x = slot_center_x - (self.temperate_climate_image.get_width() // 2)
        climate_y = slot_center_y - (self.temperate_climate_image.get_height() // 2)

        self.climate_image_pos = Vector2(climate_x, climate_y)

        # -------------------------------------------------------------------
        #                       TEXT POSITIONING
        # -------------------------------------------------------------------
        # TEMPERATURE TEXT
        # The temperature display is positioned under the climate slot.
        offset_from_slot = 20
        x = (self.climate_slot_pos.x + (self.climate_slot_edge / 2))
        y = (self.climate_slot_pos.y + self.climate_slot_edge + offset_from_slot)
        self.txt_temperature_pos = Vector2(x, y)

        # SURVIVORS ALIVE TEXT
        x = self.screen_width // 2
        y = 15  # Offset from top of screen
        self.txt_survivors_alive_pos = Vector2(x, y)

    def show(self, current_climate: Climate, temperature: float):
        """
        Display of all HUD elements.

        Args:
            current_climate (Climate): Current simulation climate
            temperature (float): Current simulation temperature
        """
        # -------------------------------------------------------------------
        #                        SET CLIMATE IMAGES
        # -------------------------------------------------------------------
        # Changes the HUD climate image to match the current simulation climate.

        self.current_climate = current_climate # Get the current climate

        # Temperate climate
        if self.current_climate == Climate.TEMPERATE:
            self.current_climate_image = self.temperate_climate_image

        # Cold climate
        elif self.current_climate == Climate.COLD:
            self.current_climate_image = self.cold_climate_image

        # Hot climate
        else:
            self.current_climate_image = self.hot_climate_image

        # -------------------------------------------------------------------
        #                            SHOW TEXT
        # -------------------------------------------------------------------
        # TEMPERATURE
        # Display of current simulation temperature under the HUD climate slot.
        print_on_screen(screen, self.txt_temperature_pos, font_size=20, txt=f"{int(temperature)}°C", bold=True)

        # SURVIVORS ALIVE
        # Displays the number of Survivors alive out of the total number of Survivors.
        total_survivors = self.watcher.init_population
        survivors_alive = self.watcher.living_survivors
        txt = f"Survivors alive : {survivors_alive}/{total_survivors}"

        print_on_screen(screen, self.txt_survivors_alive_pos, txt=txt, font_size=20, bold=True)

        # -------------------------------------------------------------------
        #                         SHOW EVERYTHING
        # -------------------------------------------------------------------
        screen.blit(self.climate_slot_image, self.climate_slot_pos)
        screen.blit(self.current_climate_image, self.climate_image_pos)