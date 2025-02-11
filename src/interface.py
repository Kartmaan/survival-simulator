import os
from typing import Optional

import pygame
from pygame.math import Vector2

from src.pygame_options import screen
from src.utils import get_distance, get_center
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
    about it.
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
    Class representing the simulation interface.

    This class is responsible for displaying visual information on the screen, such as weather conditions and survivor
    statistics.
    """
    def __init__(self):
        # -------------------------------------------------------------------
        #                           SCREEN SIZE
        # -------------------------------------------------------------------
        self.screen_width = screen.width
        self.screen_height = screen.height
        # ===================================================================
        #                             CLIMATE
        # ===================================================================
        # -------------------------------------------------------------------
        #                          CLIMATE SLOT
        # -------------------------------------------------------------------
        self.climate_slot_path: str = os.path.join("assets", 'hud', "climate_slot.png")
        self.climate_slot_image: pygame.Surface = pygame.image.load(self.climate_slot_path)
        self.climate_slot_image.set_alpha(150) # Opacity

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

        # Climate images size
        self.climate_image_pos: Vector2 = Vector2(0, 0)
        self.climate_image_slot_ratio = 0.9
        self.climate_image_size: Optional[float] = None
        self.current_climate_image: pygame.Surface = self.temperate_climate_image
        # -------------------------------------------------------------------
        #                        ENERGY MEAN GAUGE
        # -------------------------------------------------------------------
        # Colors
        self.frame_color = colors["GAUGE_FRAME"]
        self.start_color = colors["GAUGE_START"]
        self.end_color = colors["GAUGE_END"]
        self.gauge_alpha: int = 150 # Opacity

        # Position
        self.gauge_pos: Optional[Vector2] = None

        # Sizes
        self.gauge_height_ratio: float = 0.7
        self.gauge_height: float = self.screen_height * self.gauge_height_ratio
        self.gauge_width_ratio: float = 0.4
        self.gauge_width: Optional[float] = self.climate_slot_edge * self.gauge_width_ratio
        self.frame_thickness = 3

        # Values
        self.current_value: Optional[float] = None
        self.max_value: Optional[float] = None

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
        self.survivor_zero: Survivor = Survivor(0, 0)

        # -------------------------------------------------------------------
        #                       SCALING & POSITIONING
        # -------------------------------------------------------------------
        # Scaling and positioning of all elements except the gauge.
        self.scaling()
        self.positioning()

        # The gauge is scaled and positioned after the other HUD elements, since it uses the position of the climate
        # slot after its scaling and positioning.
        self.gauge_scaling()
        self.gauge_positioning()

    def interpolate_gauge_color(self, ratio:float) -> tuple[int, int, int, int]:
        """
        Interpole between two colors based on ratio.
        ratio = 1 → start color.
        ratio = 0 → end color.

        The gauge is colored 'self.start_color' when the measured value is at its maximum, and changes to
        'self.end_color' by gradient as the value decreases.

        Returns:
            tuple: Adjusted color + alpha value
        """
        r = int(self.start_color[0] * ratio + self.end_color[0] * (1 - ratio))
        g = int(self.start_color[1] * ratio + self.end_color[1] * (1 - ratio))
        b = int(self.start_color[2] * ratio + self.end_color[2] * (1 - ratio))

        return r, g, b, self.gauge_alpha

    def gauge_scaling(self):
        """
        Scales gauge.

        - Gauge width is a fraction of the width of 'climate_slot' (which has already been scaled and positioned).
        - Gauge height is a fraction of the distance from the temperature text position to the bottom of the window.
        """
        # y distance between temperature txt and screen bottom
        temp_to_bottom_dist = get_distance(self.txt_temperature_pos, Vector2(self.txt_temperature_pos.x, screen.height))
        self.gauge_height = temp_to_bottom_dist * self.gauge_height_ratio
        self.gauge_width = self.climate_slot_edge * self.gauge_width_ratio

    def gauge_positioning(self):
        """
        Gauge positioning.

        The center of the gauge is positioned at the midpoint between the temperature text and the bottom of the screen.
        """
        # Midpoint between temperature text and bottom screen
        middle = get_center(self.txt_temperature_pos, Vector2(self.txt_temperature_pos.x, screen.height))

        x = middle.x - self.gauge_width // 2
        y = middle.y - self.gauge_height // 2
        self.gauge_pos = Vector2(x, y)

    def draw_gauge(self, value: float, max_value: int):
        """
        Draws gauge on screen.

        Args:
            value (float): Value to be displayed on the gauge
            max_value (float): Maximum value of the 'value' argument. Used to adjust gauge progression.
        """
        # Size and position recovery
        x = self.gauge_pos.x
        y = self.gauge_pos.y
        width = self.gauge_width
        height = self.gauge_height

        # Creating the surface on which the gauge will be drawn
        fill_surface = pygame.Surface((width, height), pygame.SRCALPHA)

        # Gauge height adjustment based on current value and max. value
        fill_height = int((value / max_value) * (height - self.frame_thickness * 2))

        # Gauge color adjusts to current value, proportional to max. value
        fill_color = self.interpolate_gauge_color(value / max_value)

        # Drawing of gauge at height adjusted to current value
        pygame.draw.rect(fill_surface, fill_color, (0, height - fill_height, width, fill_height))

        # Gauge display
        screen.blit(fill_surface, (x, y))

        # Drawing gauge frame displayed over it
        pygame.draw.rect(screen, self.frame_color, (x, y, width, height), self.frame_thickness)

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
        #                        TEXT POSITIONING
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
        #                         SHOW CLIMATE SLOT
        # -------------------------------------------------------------------
        screen.blit(self.climate_slot_image, self.climate_slot_pos)
        screen.blit(self.current_climate_image, self.climate_image_pos)

        # -------------------------------------------------------------------
        #                            SHOW GAUGE
        # -------------------------------------------------------------------
        # Gauge title txt
        offset_from_gauge_top = 40
        title_pos_x = (self.gauge_pos.x + self.gauge_width // 2)
        title_pos_y = (self.gauge_pos.y + self.gauge_width // 2) - offset_from_gauge_top
        title_pos = Vector2(title_pos_x, title_pos_y)

        print_on_screen(screen, title_pos, txt="Energy mean", font_size=18)

        # Gauge value txt
        offset_from_gauge_bottom = 25
        value_pos_x = title_pos_x
        value_pos_y = (self.gauge_pos.y + self.gauge_height) + offset_from_gauge_bottom
        value_pos = Vector2(value_pos_x, value_pos_y)

        print_on_screen(screen, value_pos, txt=f"{round(self.watcher.energy_mean, 2)}", font_size=18)

        # Show gauge
        self.draw_gauge(self.watcher.energy_mean, self.survivor_zero.energy_default)