from pygame_options import pygame, screen
from utils import random, Vector2, current_time, get_distance
from style import colors
#from survivor import Survivor
from danger import Danger

SHOW_SCENT_FIELD = True

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
        # Position
        self.pos = Vector2(x, y)
        self.x = self.pos.x
        self.y = self.pos.y

        # Colors
        self.color = colors["FOOD"]
        self.color_full = colors["FOOD_FULL"]
        self.color_field = self.color

        # Size
        self.edge_max = 20
        self.edge_min = 8
        self.edge = self.edge_max

        self.scent_field_radius_max = self.edge * 4
        self.scent_field_radius_min = self.edge * 2
        self.scent_field_radius = self.scent_field_radius_max

        # Time management
        self.food_timers = {}

        # States
        self.full = False

        # Energy
        self.quantity_max = 1000
        self.quantity = self.quantity_max
        self.energy_bonus = 1
        self.max_eaters = 10
        self.nb_of_eaters = 0

        # Danger info
        self.danger_object: Danger = Danger(0, 0)

        # Survivors info
        #self.all_survivors = []

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

    # TODO: Find a new position for Food when self.quantity is zero.
    def find_a_new_place(self):
        """
        Find a new place for Food

        Returns:

        """

        width = screen.width
        height = screen.height
        danger_pos = self.danger_object.get_pos()
        limit_edge = self.edge_max + (self.scent_field_radius * 2)
        min_distance_from_danger = width / 4
        far_enough = False

        x = random.randint(int(limit_edge), int(width - limit_edge))
        y = random.randint(int(limit_edge), int(height - limit_edge))

        distance = get_distance(Vector2(x, y), danger_pos)

        if distance < min_distance_from_danger:
            while not far_enough:
                x = random.randint(int(limit_edge), int(width - limit_edge))
                y = random.randint(int(limit_edge), int(height - limit_edge))
                distance = get_distance(Vector2(x, y), danger_pos)

                if distance < min_distance_from_danger:
                    continue
                else:
                    far_enough = True

        self.pos = Vector2(x, y)

        self.edge = self.edge_max
        self.scent_field_radius = self.scent_field_radius_max
        self.quantity = self.quantity_max

        # for survivor in self.all_survivors:
        #     survivor.eating = False

    # TODO: Adjust self.edge according to self.quantity.
    def adjust_edge(self):
        """

        Returns:

        """
        if self.quantity <= 0:
            return self.edge_min

        edge_range = self.edge_max - self.edge_min
        quantity_ratio = self.quantity / self.quantity_max
        new_edge = self.edge_min + (edge_range * quantity_ratio)

        self.edge = new_edge

        radius_range = self.scent_field_radius_max - self.scent_field_radius_min
        new_radius = self.scent_field_radius_min + (radius_range * quantity_ratio)

        self.scent_field_radius = new_radius

    def show(self):
        food_rect = pygame.Rect(self.pos.x, self.pos.y, self.edge, self.edge)

        if self.full:
            pygame.draw.rect(screen, tuple(self.color_full), food_rect)
        else:
            pygame.draw.rect(screen, tuple(self.color), food_rect)

        if SHOW_SCENT_FIELD:
            pygame.draw.circle(screen, self.color_field, (self.pos.x + self.edge // 2, self.pos.y + self.edge // 2),
                               self.scent_field_radius, 2)

    def get_pos(self) -> Vector2:
        pos = pygame.math.Vector2(self.x + self.edge / 2, self.y + self.edge / 2)
        return pos