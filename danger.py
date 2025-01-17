from pygame_options import pygame, screen
from utils import Vector2, current_time
from style import colors

class Danger:
    """
    - The Danger is posted at a random location on the surface.
    - It has a rage level that determines the amount of damage it inflicts.
    - It attacks Survivors who get too close to it.
    - When attacking, the Danger moves rapidly back and forth in the direction of the targeted Survivor.
    - Each successful attack (probability) drains part of the Survivor's energy.
    - Each attack increases its rage level to a maximum threshold.
    - The Danger rotates on itself, its speed proportional to its rage level.
    - When the Danger spends a certain amount of time without attacking, its rage level decreases.
    """
    def __init__(self, x, y):
        self.initial_pos = Vector2(x, y)
        self.pos = self.initial_pos.copy()
        self.edge = 20
        self.color = colors["DANGER"]
        self.damage = 1
        self.nb_of_hits = 0

        self.target = None
        self.attacking = False
        self.returning = False

        self.attack_speed = 7
        self.return_speed = 6
        self.attack_duration = 0.3
        self.return_duration = 0.4

        self.angle = 0
        self.rotation_speed = 10
        self.rotation_speed_max = 30

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

    def attack(self, target_pos: Vector2):
        # Initiating the attack movement
        if not self.attacking and not self.returning:
            self.target = target_pos
            self.attacking = True
            self.danger_timers["attack"] = current_time()

        # Attack movement
        if self.attacking:
            elapsed_attack_time = current_time() - self.danger_timers["attack"]
            if elapsed_attack_time <= self.attack_duration:
                direction = (self.target - self.pos)
                if direction.length() > 0:  # Avoid zero vector
                    direction = direction.normalize()
                    self.pos += direction * self.attack_speed
            else:
                self.attacking = False
                self.returning = True
                self.danger_timers["return"] = current_time()

        # Return movement
        if self.returning:
            elapsed_return_time = current_time() - self.danger_timers["return"]
            if elapsed_return_time <= self.return_duration:
                direction = (self.initial_pos - self.pos)
                if direction.length() > 0:  # Avoid zero vector
                    direction = direction.normalize()
                    self.pos += direction * self.return_speed
            else:
                self.nb_of_hits += 1
                self.returning = False
                self.pos = self.initial_pos.copy()

    def show(self):
        x = self.pos.x
        y = self.pos.y

        danger_rect = pygame.Rect(x, y, self.edge, self.edge)

        surface = pygame.Surface(danger_rect.size, pygame.SRCALPHA)
        surface.fill(tuple(self.color))

        rotated_surface = pygame.transform.rotate(surface, self.angle)
        rotated_rect = rotated_surface.get_rect(center=danger_rect.center)

        self.angle += self.rotation_speed

        screen.blit(rotated_surface, rotated_rect)
        # pygame.draw.rect(screen, tuple(self.color), danger_rect)

    def get_pos(self) -> Vector2:
        pos = self.pos.x + self.edge // 2, self.pos.y + self.edge // 2
        return pygame.math.Vector2(pos)

def get_danger_model() -> Danger:
    danger = Danger(0, 0)
    return danger