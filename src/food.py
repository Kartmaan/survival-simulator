import logging

import pygame
from pygame.math import Vector2
import numpy as np

from src.pygame_options import screen
from src.utils import current_time, get_distance
from src.style import colors
from src.danger import Danger

logger = logging.getLogger("src.debug")
SHOW_SCENT_FIELD = False

class Food:
    """
    Food consumed by Survivors to boost their energy levels.

    - Food has an olfactory field that can be detected by the Survivor's sensory field.
    - It has a quantity value that decreases as it is consumed by Survivors.
    - The olfactory field shrinks as food is consumed.
    - When its energy value reaches zero, Food disappears to appear somewhere else after a given time.
    - A limited number of Survivors can consume the Food simultaneously.
    """
    def __init__(self, x, y):
        # -------------------------------------------------------------------
        #                             POSITION
        # -------------------------------------------------------------------
        self.pos = Vector2(x, y)
        self.x = self.pos.x
        self.y = self.pos.y

        # -------------------------------------------------------------------
        #                              COLOR
        # -------------------------------------------------------------------
        self.color = colors["FOOD"]
        self.color_full = colors["FOOD_FULL"]
        self.color_finished = colors["FOOD_FINISHED"] # Food completely consumed
        self.color_field = self.color

        # -------------------------------------------------------------------
        #                              SIZE
        # -------------------------------------------------------------------
        self.edge_max = 20
        self.edge_min = 8
        self.edge = self.edge_max

        self.scent_field_radius_max = self.edge * 4
        self.scent_field_radius_min = self.edge * 2
        self.scent_field_radius = self.scent_field_radius_max

        # -------------------------------------------------------------------
        #                         TIME MANAGEMENT
        # -------------------------------------------------------------------
        self.food_timers = {}
        self.time_to_respawn = 5
        self.time_to_respawn_penalty = 1
        self.decay_frequency = 0.5

        # -------------------------------------------------------------------
        #                              STATUS
        # -------------------------------------------------------------------
        self.full = False
        self.in_cooldown = False

        # -------------------------------------------------------------------
        #                        QUANTITY MANAGEMENT
        # -------------------------------------------------------------------
        self.quantity_penalty = 1
        self.quantity_max = 200
        self.quantity_min = 30
        self.init_quantity = self.define_quantity()
        self.quantity = self.init_quantity

        self.energy_bonus = 1
        self.max_eaters = 10

        self.decay_amount = 0.5
        self.decay_amount_penalty = 1

        # -------------------------------------------------------------------
        #                           OTHER OBJECTS
        # ------------------------------------------------------------------
        # Danger info
        self.danger_object: Danger = Danger(0, 0)

    def timer(self, timer_name: str, duration: float) -> bool:
        """Checks if a timer has expired.

        This allows Food to have its own timers and therefore to have a personalized time management system
        for each of them.

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

    def find_a_new_place(self):
        """
        Find a new place for Food.

        The Danger position is used to ensure that the new coordinates are far enough away from it.
        """
        width = screen.width
        height = screen.height

        danger_pos = self.danger_object.get_pos()
        limit_edge = self.edge_max + (self.scent_field_radius * 2)
        min_distance_from_danger = width / 4
        far_enough = False

        # Naive attempt
        x = np.random.randint(int(limit_edge), int(width - limit_edge))
        y = np.random.randint(int(limit_edge), int(height - limit_edge))

        distance = get_distance(Vector2(x, y), danger_pos)

        if distance < min_distance_from_danger:
            while not far_enough:
                x = np.random.randint(int(limit_edge), int(width - limit_edge))
                y = np.random.randint(int(limit_edge), int(height - limit_edge))
                distance = get_distance(Vector2(x, y), danger_pos)

                if distance < min_distance_from_danger:
                    logger.info("Food respawn : Food too close from Danger avoided")
                    continue
                else:
                    far_enough = True

        self.pos = Vector2(x, y)
        self.x = self.pos.x
        self.y = self.pos.y

        self.edge = self.edge_max
        self.scent_field_radius = self.scent_field_radius_max
        self.quantity = self.define_quantity()
        self.init_quantity = self.quantity
        self.full = False
        self.in_cooldown = False

        logger.info(f"Food respawn at {self.pos}. Quantity : {self.quantity}")

    def spoil_and_respawn(self, survivors:list):
        """
        Degrades food at regular intervals and respawns it at new coordinates when its quantity reaches zero.

        Args:
            survivors (list[Survivor]) : List of Survivors who will receive the new state of the Food object after its
            respawn.
        """
        # Food spoils at regular intervals, whether it's eaten or not.
        if self.timer("decay", self.decay_frequency):
            if self.quantity > 0:
                self.quantity -= self.decay_amount * self.decay_amount_penalty # Climatic penalty
                self.adjust_size()

        # The food was completely consumed
        if self.quantity <= 0:
            if not self.in_cooldown:
                self.food_timers["cooldown"] = current_time()
                self.in_cooldown = True

            # All eating Survivors disengage from the food for a while.
            for eating_survivor in survivors:
                if eating_survivor.eating or eating_survivor.food_rush:
                    eating_survivor.appetite_suppressant_pill()

            # Cooldown launched for Food respawn
            cooldown = self.time_to_respawn * self.time_to_respawn_penalty # Climatic penalty
            if self.timer("cooldown", cooldown):
                self.find_a_new_place()
                self.in_cooldown = False
            else:
                self.in_cooldown = True

            # The new Food status is sent to all Survivors.
            for not_eating_survivor in survivors:
                not_eating_survivor.food_object = self

        else:
            self.in_cooldown = False

    def define_quantity(self) -> int:
        """
        Set a random food quantity.
        """
        random_quantity = np.random.randint(self.quantity_min, self.quantity_max) * self.quantity_penalty
        return random_quantity

    def adjust_size(self):
        """
        Reduces 'self.edge' and 'self.scent_field_radius' according to 'self.quantity value'.

        The reduction is linear and proportional to quantity, between the maximum and minimum values defined for each
        attribute. When `self.quantity` reaches 0, `self.edge` and `self.scent_field_radius` reach their respective
        minimum values (`self.edge_min` and `self.scent_field_radius_min`).
        """
        quantity_ratio = self.quantity / self.quantity_max

        # Edge reduction
        if self.quantity > 0:
            edge_range = self.edge_max - self.edge_min
            new_edge = self.edge_min + (edge_range * quantity_ratio)

            self.edge = new_edge
        else:
            self.edge = self.edge_min

        # Scent radius reduction
        if self.quantity > 0:
            radius_range = self.scent_field_radius_max - self.scent_field_radius_min
            new_radius = self.scent_field_radius_min + (radius_range * quantity_ratio)

            self.scent_field_radius = new_radius
        else:
            self.scent_field_radius = self.scent_field_radius_min

    def show(self):
        """
        Display Food on screen.
        """
        food_rect = pygame.Rect(self.pos.x, self.pos.y, self.edge, self.edge)

        # Changes color depending on whether Food is full or not.
        if self.full:
            pygame.draw.rect(screen, tuple(self.color_full), food_rect)
        elif self.in_cooldown:
            pygame.draw.rect(screen, tuple(self.color_finished), food_rect)
        else:
            pygame.draw.rect(screen, tuple(self.color), food_rect)

        if SHOW_SCENT_FIELD:
            pygame.draw.circle(screen, self.color_field,
                               (self.pos.x + self.edge // 2, self.pos.y + self.edge // 2),
                               self.scent_field_radius, 2)

    def get_pos(self) -> Vector2:
        """
        Returns Food's coordinates.
        """
        pos = Vector2(self.x + self.edge / 2, self.y + self.edge / 2)
        return pos