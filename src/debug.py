import pygame
import logging

from src.pygame_options import screen
from src.utils import current_time
from src.style import colors

HEIGHT = screen.height
log_file_name = "logging.log"
logging_level_terminal = logging.ERROR # DEBUG, INFO, WARNING, ERROR, CRITICAL

def logging_config():
    """
    Creates a Logger object that can be called by other project files.

    Logs of all levels are saved in the 'logging.log' file, but only those of WARNING level or higher are displayed
    on the terminal.
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG) # All levels

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # All levels are saved in the file
    # The log file is overwritten each time the program is launched.
    file_handler = logging.FileHandler(log_file_name, mode='w')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # Only logs of WARNING level or higher are displayed on the terminal.
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging_level_terminal)
    stream_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger

logger = logging_config()

class DebugOnScreen:
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
        self.offset = 25
        self.size_height_ratio = 0.2
        self.font = pygame.font.SysFont(self.font_name, self.font_size)
        self.debug_timers = {}

    def __len__(self):
        return len(self.debug_txt)

    def timer(self, timer_name: str, duration: float) -> bool:
        """Checks if a timer has expired.

        This timer is used to prevent certain logger from being displayed too frequently.

        Args:
            timer_name (str): Timer name.
            duration (float): Desired duration in seconds.

        Returns:
            bool: True if time is up, False otherwise.
        """
        now = current_time()

        if timer_name not in self.debug_timers:
            self.debug_timers[timer_name] = now
            return False

        elapsed_time = now - self.debug_timers[timer_name]
        if elapsed_time >= duration:
            self.debug_timers[timer_name] = now
            return True

        return False

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
        Displays all debug entries on screen.
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
