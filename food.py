from pygame_options import pygame, screen
from utils import Vector2, current_time, get_distance
from style import colors

SHOW_SCENT_FIELD = False

class Food:
    """
    - Food has an odor field that can be detected by the Survivor's sensory field.
    - It has an energy value that decreases as it is consumed by Survivors.
    - When its energy value reaches zero, it disappears.
    - There are several types of Food with different energy values, some of which can also be poisonous.
    - A limited number of Survivors can consume the Food simultaneously
    - If the Food is not consumed, it rots. The scent field narrows, the energy level drops and the Food disappears.
    """
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.color = colors["FOOD"]
        self.color_field = self.color
        self.edge = 20
        self.scent_field_radius = self.edge * 2
        self.energy = 20
        self.energy_bonus = 1
        self.max_eaters = 5
        self.nb_of_eaters = 0
        self.full = False
        self.food_timers = {}

    def timer(self, timer_name: str, duration: float) -> bool:
        """Checks if a timer has expired.

        This allows Food to have its own timers
        and therefore to have a personalized time management
        system for each of them.

        Args:
            timer_name (str): Timer name.
            duration (float): Desired duration in seconds.

        Returns:
            bool: True if time is up, False otherwise.
        """
        now = current_time()

        if timer_name not in self.food_timers:
            self.food_timers[timer_name] = now
            return False

        elapsed_time = now - self.food_timers[timer_name]
        if elapsed_time >= duration:
            self.food_timers[timer_name] = now
            return True

        return False

    def how_many_eaters(self, survivors_list: list):
        eaters = 0
        for survivor in survivors_list:
            # distance = get_distance(self.get_pos(), survivor.get_pos())
            # if distance <= self.scent_field_radius and survivor.eating:
            #     eaters += 1
            if survivor.eating:
                eaters += 1

        self.nb_of_eaters = eaters

    def show(self):
        food_rect = pygame.Rect(self.x, self.y, self.edge, self.edge)
        pygame.draw.rect(screen, tuple(self.color), food_rect)
        if SHOW_SCENT_FIELD:
            pygame.draw.circle(screen, self.color_field, (self.x + self.edge // 2, self.y + self.edge // 2), self.scent_field_radius, 2)

    def get_pos(self) -> Vector2:
        pos = pygame.math.Vector2(self.x + self.edge / 2, self.y + self.edge / 2)
        return pos

def get_food_model() -> Food:
    food = Food(0, 0)
    return food