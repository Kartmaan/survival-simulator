import pygame
from pygame.math import Vector2

colors = {
    "WHITE" : [255, 255, 255],
    "BLACK" : [0, 0, 0],
    "RED" : [255, 0, 0],
    "GREEN" : [0, 255, 0],
    "BLUE" : [0, 0, 255],
    "ORANGE" : [255, 128, 0],

    "BACKGROUND_COLOR" : [204, 229, 255],

    "SURVIVOR_NORMAL" : [76, 180, 0],
    "SURVIVOR_FOLLOW" : [255, 128, 0],
    "SURVIVOR_CRITICAL" : [34, 55, 89],
    "SURVIVOR_NOT_ABLE" : [153, 0, 153], # Not able to eat
    "SURVIVOR_EATING" : [153, 51, 255],

    "FOOD" : [0, 128, 255],
    "FOOD_FULL" : [96, 96, 96],
    "FOOD_FINISHED" : [192, 192, 192],

    "DANGER" : [255, 51, 51, 255], # ALPHA

    "INTERFACE" : [176,224,230],
    "SHOWCASE" : [240,255,240]
}

def print_on_screen(screen: pygame.Surface, pos: Vector2 = Vector2(0, 0), ref_pos: str = "center",
                    font_name: str = "Arial", font_size: int = 20, txt: str = "", color: tuple|list = (0,0,0)):
    """
    Displays text directly on screen.

    Args:
        screen (pygame.Screen) : Surface where to print
        pos (Vector2) : Text coordinates. Default : Vector2(0, 0).
        ref_pos (str) : Coordinate referential ('center', 'topleft', 'topright'). Default : "center"
        font_name (str) : Font name. Default : "Arial".
        font_size (int) : Font size. Default : 20.
        txt (str) : Text to display. Default : "".
        color (tuple|list) : Text color RGB. Default : (0,0,0).
    """
    font = pygame.font.SysFont(font_name, font_size)
    txt_surface = font.render(txt, antialias=True, color=color)
    txt_rect = txt_surface.get_rect()

    if ref_pos == "center":
        txt_rect.center = pos
    elif ref_pos == "topleft":
        txt_rect.topleft = pos
    elif ref_pos == "topright":
        txt_rect.topright = pos
    else:
        txt_rect.center = pos

    screen.blit(txt_surface, txt_rect)

def draw_cross(screen: pygame.Surface, pos: Vector2, branch_length: int, width: int = 1, color: tuple = (0,0,0)):
    """
    Draws a cross on the screen at the specified coordinates.

    Args:
        screen (Surface): Surface on which to draw the cross.
        pos (Vector2): Cross coordinates
        branch_length (int): Length of cross branches
        width (int): Branch thickness
        color (tuple): Cross color
    """
    first_branch = [(pos.x - branch_length, pos.y - branch_length), (pos.x + branch_length, pos.y + branch_length)]
    second_branch = [(pos.x - branch_length, pos.y + branch_length), (pos.x + branch_length, pos.y - branch_length)]

    pygame.draw.line(screen, color, first_branch[0], first_branch[1], width)
    pygame.draw.line(screen, color, second_branch[0], second_branch[1], width)

def draw_square(screen: pygame.Surface, pos: Vector2, edge: int, color: tuple = (0,0,0)):
    """
    Draws a square centered on the given position.

    Args:
        screen (Surface): Surface on which to draw the square.
        pos (Vector2): Square coordinates.
        edge (int): Square side length.
        color (tuple): Square color.
    """
    rect = pygame.Rect(pos.x, pos.y, edge, edge)
    rect.center = pos
    pygame.draw.rect(screen, color, rect)