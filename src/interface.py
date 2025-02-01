import pygame
from pygame.math import Vector2

from src.pygame_options import screen
from src.style import colors, print_on_screen
from src.survivor import Survivor

WIDTH, HEIGHT = screen.get_size()

def show_winners_stats(surface: pygame.Surface, start_pos: Vector2, winner: Survivor):
    """
    Displaying the winner's statistics.
    """
    line_spacing = 50
    font_size = 35

    stats = {
        "Audacity" : round(winner.audacity, 2),
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