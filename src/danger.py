import logging

import pygame
from pygame.math import Vector2

from src.pygame_options import screen
from src.utils import current_time
from src.style import colors

logger = logging.getLogger("src.debug")

class Danger:
    """
    Entity attacking Survivor for unknown reason.

    - The Danger is posted at a random location on the surface.
    - It has a rage level that determines the amount of damage it inflicts.
    - It attacks Survivors who get too close to it.
    - When attacking, the Danger moves rapidly back and forth in the direction of the targeted Survivor.
    - Todo: Each successful attack (probability) drains part of the Survivor's energy.
    - Each attack increases its rage level to a maximum threshold.
    - The Danger rotates on itself, its speed proportional to its rage level.
    - When the Danger spends a certain amount of time without attacking, its rage level decreases.
    """
    def __init__(self, x, y):
        # Position
        self.initial_pos = Vector2(x, y)
        self.pos = self.initial_pos.copy()

        # Colors
        self.color = colors["DANGER"]

        # Size
        self.edge = 20

        # Attack
        self.damage = 1
        self.nb_of_hits = 0
        self.rage = 0
        self.target = None
        self.in_cooldown = False
        self.attacking = False
        self.returning = False

        # Speed
        self.attack_speed = 7
        self.return_speed = 6
        self.rotation_speed = 0
        self.rotation_speed_max = 30
        self.angle = 0

        # Time management
        self.attack_cooldown = 2
        self.rage_decreasing_cooldown = 2
        self.attack_duration = 0.2
        self.return_duration = 0.5
        self.danger_timers = {}

    def timer(self, timer_name: str, duration: float) -> bool:
        """Checks if a timer has expired.

        This allows Danger to have its own timers
        and therefore to have a personalized time management
        system for each of them.

        Args:
            timer_name (str): Timer name.
            duration (float): Desired duration in seconds.

        Returns:
            bool: True if time is up, False otherwise.
        """
        now = current_time()

        if timer_name not in self.danger_timers:
            self.danger_timers[timer_name] = now
            return False

        elapsed_time = now - self.danger_timers[timer_name]
        if elapsed_time >= duration:
            self.danger_timers[timer_name] = now
            return True

        return False

    # TODO: Cooldown for attack
    def attack(self, target_pos: Vector2):
        """
        Triggering the attack animation against a Survivor.

        This animation consists of a rapid back-and-forth movement towards the targeted Survivor.

        Args:
            target_pos (Vector2): Targeted Survivor position.
        """
        # Initiating the attack movement
        if not self.attacking and not self.returning:
            self.target = target_pos
            self.attacking = True
            self.danger_timers["attack"] = current_time()

        # Attack movement (towards the target)
        if self.attacking:
            elapsed_attack_time = current_time() - self.danger_timers["attack"]
            if elapsed_attack_time <= self.attack_duration:
                direction = (self.target - self.pos)
                if direction.length() > 0:  # Avoid zero vector
                    direction = direction.normalize()
                    self.pos += direction * self.attack_speed
                else:
                    logger.critical("Danger attack : null vector")
            else:
                self.attacking = False
                self.returning = True
                self.danger_timers["return"] = current_time()

        # Return movement (to initial position)
        if self.returning:
            elapsed_return_time = current_time() - self.danger_timers["return"]
            if elapsed_return_time <= self.return_duration:
                direction = (self.initial_pos - self.pos)
                if direction.length() > 0:  # Avoid zero vector
                    direction = direction.normalize()
                    self.pos += direction * self.return_speed

            # When the return movement is complete, the attack is considered successful, increasing the Danger's
            # rage level.
            else:
                self.nb_of_hits += 1
                if self.rotation_speed < self.rotation_speed_max:
                    self.rotation_speed += 1
                    self.rage +=1

                    # We create a time stamp of the moment of the attack, so that we can check the expiration of
                    # self.rage_decreasing_cooldown
                    self.danger_timers["rage_cooldown"] = current_time()

                self.returning = False
                self.pos = self.initial_pos.copy()

    def rage_cooldown(self):
        """
        Decreases rage level, as well as rotation speed, if the Danger has not attacked for a number of seconds
        determined by the attribute self.rage_decreasing_cooldown.
        """
        if "rage_cooldown" in self.danger_timers:
            if self.timer("rage_cooldown", self.rage_decreasing_cooldown):
                if self.rotation_speed > 0:
                    self.rotation_speed -= 1
                    self.rage -= 1

    def show(self):
        """
        Displays Danger on the screen.
        """
        #
        self.rage_cooldown()

        x = self.pos.x
        y = self.pos.y

        pygame.draw.circle(screen, colors["BLACK"], (x + self.edge / 2, y + self.edge / 2), self.edge // 4)

        danger_rect = pygame.Rect(x, y, self.edge, self.edge)

        surface = pygame.Surface(danger_rect.size, pygame.SRCALPHA)
        surface.fill(tuple(self.color))

        rotated_surface = pygame.transform.rotate(surface, self.angle)
        rotated_rect = rotated_surface.get_rect(center=danger_rect.center)

        self.angle += self.rotation_speed

        screen.blit(rotated_surface, rotated_rect)
        # pygame.draw.rect(screen, tuple(self.color), danger_rect)

    def get_pos(self) -> Vector2:
        """
        Returns Danger coordinates

        Returns:
            Vector2 : Danger coordinates
        """
        pos = self.pos.x + self.edge // 2, self.pos.y + self.edge // 2
        return pygame.math.Vector2(pos)