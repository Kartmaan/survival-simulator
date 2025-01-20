from pygame_options import pygame, screen
from style import colors

HEIGHT = screen.height

class DebugText:
    """
    Adds debug data and displays it on screen.
    """
    def __init__(self):
        self.init_x = 10
        self.init_y = 10
        self.debug_txt = {}
        self.font_name = "Arial"
        self.font_size = 20
        self.font_color = colors["BLACK"]
        self.font_size_max = self.font_size
        self.offset = 20
        self.size_height_ratio = 1.3
        self.font = pygame.font.SysFont(self.font_name, self.font_size)

    def __len__(self):
        return len(self.debug_txt)

    def add(self, title: str, value):
        """
        Adds a new entry to the debug display.

        Args:
            title: Entry title
            value: Entry value
        """
        self.debug_txt[title] = value

    def enough_space(self) -> bool:
        """
        Checks whether the vertical axis of the surface is large enough to display all entries with the default
        font size

        Returns:
            True : Enough space
            False : Not enough space
        """
        nb_of_lines = len(self.debug_txt)
        if nb_of_lines == 0:
            return True

        total_height = (nb_of_lines * (self.font_size * self.size_height_ratio)) + ((nb_of_lines - 1) * self.offset)

        return total_height <= HEIGHT

    def adjust_size(self):
        """
        If the vertical axis of the surface isn't large enough to display all entries, the font size is reduced so
        that all entries can be displayed.
        """
        nb_of_lines = len(self.debug_txt)
        self.font_size = int((HEIGHT - (nb_of_lines - 1) * self.offset) / (self.size_height_ratio * nb_of_lines))
        self.font = pygame.font.SysFont(self.font_name, self.font_size)

    def show(self):
        """
        Displays all debug entries.
        """
        if not self.enough_space():
            self.adjust_size()

        x = self.init_x
        y = self.init_y
        for title, value in self.debug_txt.items():
            txt_surface = self.font.render(f"{title} : {value}", True, self.font_color)
            txt_rect = txt_surface.get_rect()
            txt_rect.topleft = (x, y)
            screen.blit(txt_surface, txt_rect)
            y += self.offset