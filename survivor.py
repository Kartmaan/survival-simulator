from pygame_options import pygame, screen, WIDTH, HEIGHT
from utils import Vector2, current_time, get_distance, np
from style import colors
from food import Food

SHOW_SENSORIAL_FIELD = False
food_zero = Food(0, 0)

class Survivor:
    """
    - The Survivor has a limited amount of energy
    - It moves randomly across the surface, which causes it to lose energy.
    - It has a sensory field that enables it to detect food, danger and other Survivors.
    - When he detects danger, he flees, increasing his speed and losing more energy.
    - When it detects another Survivor fleeing, it follows it out of survival instinct.
    - When it detects food and the need arises, it consumes it to increase its energy.
    - A Survivor with a critical energy threshold consumes food more quickly.
    - If a Survivor's energy reaches a critical threshold, its speed is reduced and its sensory field gradually narrows.
    - If energy reaches zero, the Survivor stops and disappears.
    """

    def __init__(self, x, y):
        # Position / Direction
        self.pos = Vector2(x, y)
        self.x = self.pos.x
        self.y = self.pos.y
        self.dx = 0.0
        self.dy = 0.0

        # Speed
        self.speed_default = 4
        self.speed = self.speed_default
        self.speed_critical = self.speed / 4
        self.speed_food_rush = self.speed + 1
        self.speed_flee = self.speed + 2
        self.speed_flee_critical = self.speed_critical + 2

        # Time management
        self.survivor_timers = {}
        self.direction_duration_min = 2
        self.direction_duration_max = 7
        self.flee_duration = 3
        self.fade_duration = 5
        self.immobilization_time = 5
        self.eating_cooldown = 5

        # Size
        self.survivor_radius_default = 4
        self.survivor_radius = self.survivor_radius_default
        self.survivor_radius_eating = self.survivor_radius + 3
        self.sensorial_radius_default = self.survivor_radius * 8
        self.sensorial_radius = self.survivor_radius_default

        # Colors
        self.color = colors["SURVIVOR_NORMAL"]
        self.color_eating = colors["SURVIVOR_EATING"]
        self.color_not_able = colors["SURVIVOR_NOT_ABLE"]
        self.color_danger = colors["RED"]
        self.color_follow = colors["SURVIVOR_FOLLOW"]
        self.color_critical = colors["SURVIVOR_CRITICAL"]
        self.color_immobilized = self.color_critical.copy()
        self.final_fading_color = colors["BACKGROUND_COLOR"]
        self.sensorial_field_color = colors["BLACK"]
        self.sensorial_field_color_follow = colors["ORANGE"]
        self.sensorial_field_color_danger = colors["RED"]
        self.sensorial_field_color_critical = colors["BLACK"]

        # States
        self.food_rush = False
        self.eating = False
        self.able_to_eat = True
        self.hungry = False
        self.in_danger = False
        self.in_follow = False
        self.in_critical = False
        self.immobilized = False
        self.fading = False

        # Energy management
        self.energy_default = 20
        self.energy = self.energy_default
        self.energy_hungry = self.energy_default / 2
        self.energy_critical = self.energy_default / 4
        self.energy_loss_normal = 0.5  # Per second
        self.energy_loss_rush = 0.7 # Per second
        self.energy_loss_follow = 1  # Per second
        self.energy_loss_danger = 1.5  # Per second
        self.energy_loss_frequency = 1  # In second
        self.energy_bonus_frequency = 0.5  # In second
        self.energy_bonus_frequency_critical = 0.25

        # Food info
        self.food_object: Food = Food(0, 0)

    def timer(self, timer_name: str, duration: float) -> bool:
        """Checks if a timer has expired.

        This allows each Survivor to have its own timers
        and therefore to have a personalized time management
        system for each of them.

        Args:
            timer_name (str): Timer name.
            duration (float): Desired duration in seconds.

        Returns:
            bool: True if time is up, False otherwise.
        """
        # Pygame's get_ticks() method is used to retrieve
        # the number of milliseconds that have elapsed
        # since Pygame was initialized. For each call,
        # this therefore corresponds to the current time.
        # The value is divided by 1000 to obtain seconds.
        now = current_time()

        # If the timer name isn't present in the
        # 'self.timers' dictionary keys, it's added, with
        # the current time as value (it acts as a fixed
        # time reference point for calculating durations).
        # The function returns False, as the timer has
        # just been added and therefore cannot have
        # already elapsed.
        if timer_name not in self.survivor_timers:
            self.survivor_timers[timer_name] = now
            return False

        # We assume that the timer name is already present
        # in self.timers.
        # The time stored in the dictionary is subtracted
        # from the current time to establish the elapsed
        # time.
        # If the elapsed time is greater than the desired
        # duration, then the dictionary value is updated
        # and the function returns True.
        # Otherwise, the function returns False.
        elapsed_time = now - self.survivor_timers[timer_name]
        if elapsed_time >= duration:
            self.survivor_timers[timer_name] = now
            return True

        return False

    def _change_direction(self):
        """Choosing a random direction by randomly changing
        the values of dx and dy.

        In the 'move' method, the Survivor's x and y
        values are added to dx and dy respectively,
        which can be between -1 and 1, to establish the
        direction of the next step. The variation in x
        and y can therefore be positive or negative.
        """
        angle = np.random.uniform(0, 2 * np.pi)
        self.dx = np.cos(angle)
        self.dy = np.sin(angle)

    def _critical_mode(self):
        # The Survivor has reached a critical energy level,
        # his speed is reduced and his sensory field shrinks.

        if self.energy <= self.energy_critical:
            self.in_critical = True
            self.speed = self.speed_critical
        # Survivor's energy level is high enough.
        else:
            self.in_critical = False
            self.speed = self.speed_default

        # As Survivor's energy level becomes critical, the radius of
        # his sensory field shrinks.
        if self.in_critical and self.sensorial_radius > self.survivor_radius:
            if self.timer("sensorial_radius", 0.5):
                self.sensorial_radius = max(self.survivor_radius,
                                            (self.energy / self.energy_critical) * self.sensorial_radius_default)

        elif not self.in_critical:
            self.sensorial_radius = self.sensorial_radius_default

    def _search_mode(self, conditions: list[bool]):
        if all(conditions):
            self.x += self.dx * self.speed
            self.y += self.dy * self.speed

            # As the Survivor moves, it loses energy.
            # In order to control the frequency of energy loss,
            # puncture is done in a timer.
            if self.timer("energy_loss", self.energy_loss_frequency):
                if self.in_follow:
                    self.energy -= self.energy_loss_follow
                else:
                    self.energy -= self.energy_loss_normal

            # The change of direction takes place in a timer of random
            # duration, so the Survivor will hold its directions for
            # different lengths of time.
            if self.timer("direction", np.random.uniform(self.direction_duration_min,
                                                      self.direction_duration_max)):
                if not self.food_rush and not self.eating:
                    self._change_direction()

    def _danger_mode(self):
        """
        Defines Survivor behavior when in_danger mode.
        """
        # Survivor is in danger and flees
        if self.in_danger:
            if not self.in_critical:
                self.x += self.dx * self.speed_flee
                self.y += self.dy * self.speed_flee
            else:
                self.x += self.dx * self.speed_flee_critical
                self.y += self.dy * self.speed_flee_critical

            # Energy loss in danger mode.
            if self.timer("energy_loss", self.energy_loss_frequency):
                self.energy -= self.energy_loss_danger

            # Flee duration
            if self.timer("flee", self.flee_duration):
                self.in_danger = False

    def _surface_overrun(self):
        """
        Defines the Survivor's behavior when it exceeds the limits of the surface.

        If the Survivor exits on one side of the surface, it exits on the other.
        """

        # Exits from left or right side
        if self.x + self.survivor_radius < 0:
            self.x = WIDTH + self.survivor_radius
        elif self.x - self.survivor_radius > WIDTH:
            self.x = -self.survivor_radius

        # Exits from top or bottom side
        if self.y + self.survivor_radius < 0:
            self.y = HEIGHT + self.survivor_radius
        elif self.y - self.survivor_radius > HEIGHT:
            self.y = -self.survivor_radius

    def move(self) -> bool:
        """Moves the Survivor in different modes:
            - Search mode: the Survivor moves randomly across the surface in search of food.
            - Rush mode : Survivor perceives food and rushes towards it.
            - Eating mode : The Survivor no longer moves while he recovers energy.
            - Escape mode: the Survivor perceives danger in its sensory field, and flees by increasing its speed.
            - Critical mode: the Survivor has reached a critical energy threshold, and its movement speed decreases.
            - Immobilized mode: Survivor has no energy left and can't move anymore.

            The method returns Booleans to indicate whether the Survivor should be deleted (True) or not (False).

            Returns:
                bool: Returns True if the Survivor is to be deleted, False otherwise.
        """
        # ALL STATES :
        # food_rush, eating, hungry, in_danger, in_follow, in_critical, immobilized, fading, able_to_eat
        conditions_to_search = [not self.in_danger, not self.eating, not self.food_rush]
        conditions_to_rush = [not self.in_danger, not self.in_follow, not self.immobilized, self.able_to_eat]

        # - - - - - - - - - -  IMMOBILIZATION - - - - - - - - - -

        # The Survivor has run out of energy but has not
        # yet been immobilized.
        if self.energy <= 0 and not self.immobilized:
            self.immobilized = True
            self.survivor_timers["immobilization"] = pygame.time.get_ticks() / 1000.0

        # The Survivor is immobilized.
        if self.immobilized:
            if self.timer("immobilization", self.immobilization_time):
                self.fading = True
                # The next step after immobilization is the
                # degradation of the Survivor's color, a step
                # that lasts 'self.fade_duration' seconds.
                # We therefore initialize a 'fade' timer now.
                self.survivor_timers["fade"] = current_time()

        # Start of fading phase.
        # The Survivor is immobilized and its color begins
        # to fade, the last step before it is removed.
        if self.fading:
            # Calculating the time elapsed since fading began.
            elapsed_fade_time = current_time() - self.survivor_timers["fade"]

            # The ratio of elapsed fade time to total fade time is
            # used to determine whether the fade phase is complete,
            # and also to adjust RGB values according to fade progress.
            fade_progress = elapsed_fade_time / self.fade_duration
            # print(f"elapsed_fade_time: {elapsed_fade_time}, fade_progress: {fade_progress}")

            # When the ratio is 1, this means that the time allocated
            # to fading has elapsed, but depending on the FPS value,
            # it's possible that the step between each loop passage
            # is too large, so that “fade_progress” never reaches 1.
            # To compensate for this, we add a tolerance value.
            # If the condition is True, the function stops by
            # returning True, which will send a signal (in the main
            # loop) to delete the Survivor.
            tolerance = 1e-2
            if fade_progress >= 1 - tolerance:
                return True  # Survivor will be deleted (main loop)

            # The fading phase is still in progress.
            # fade_progress' is used as a coefficient to control
            # fading of RGB values.
            else:
                r = int(self.color_critical[0] + (self.final_fading_color[0] - self.color_critical[0]) * fade_progress)
                g = int(self.color_critical[1] + (self.final_fading_color[1] - self.color_critical[1]) * fade_progress)
                b = int(self.color_critical[2] + (self.final_fading_color[2] - self.color_critical[2]) * fade_progress)
                self.color_immobilized = [r, g, b]

        # The function stops because no movement needs to be initiated
        # since the Survivor is immobilized. However, it does not need
        # to be deleted yet, since it is still in the fading phase,
        # which is why False is returned.
        if self.immobilized or self.fading:
            return False

        # - - - - - - - - - - MOVEMENT - - - - - - - - - -
        # - - - - CRITICAL MODE
        # The Survivor has reached a critical energy level, his speed is reduced and his sensory field shrinks.
        self._critical_mode()

        # - - - - SEARCH MODE
        # The Survivor has enough energy to randomly move at normal speed
        # searching for Food.
        self._search_mode(conditions_to_search)

        # - - - - FOOD RUSH MODE
        if all(conditions_to_rush):
            # The Survivor heads towards the Food coordinates.
            if self.food_rush and not self.eating:
                direction = (self.food_object.pos - self.get_pos())
                if direction.length() > 0:
                    direction = direction.normalize()

                self.dx = direction.x
                self.dy = direction.y

                self.x += self.dx * self.speed_food_rush
                self.y += self.dy * self.speed_food_rush

                distance = get_distance(self.get_pos(), self.food_object.pos)

                # The Survivor must stop short of the Food coordinates to avoid wallowing pitifully on them.
                # It stops in the olfactory field of the Food at a reasonable distance from it for greater visual
                # clarity.
                #if self.food_field >= distance >= self.food_field / 2:
                if distance <= self.food_object.scent_field_radius / 2:
                    self.food_rush = False
                    self.eating = True

                    return False

            # The rush is over and the Survivor begins to consume the Food.
            elif not self.food_rush and self.eating:
                if self.in_critical:
                    bonus_frequency = self.energy_bonus_frequency_critical
                else:
                    bonus_frequency = self.energy_bonus_frequency

                # The energy bonus occurs at a specific frequency
                if self.timer("energy_bonus", bonus_frequency):
                    self.energy += self.food_object.energy_bonus

                    if self.food_object.quantity > 0:
                        self.food_object.quantity -= self.food_object.energy_bonus
                        self.food_object.adjust_edge()
                    else:
                        #self.food_object.all_survivors = []
                        #self.food_object.find_a_new_place()
                        pass

                # If the Survivor has recovered enough energy, he stops eating. Its 'able_to_eat' state is set False
                # to start the cooldown (in the main loop) determining when it will be able to eat again.
                if self.energy >= self.energy_default:
                    self.hungry = False
                    self.eating = False
                    self.able_to_eat = False
                    self.survivor_timers["eating_cooldown"] = current_time()

                # No movement as long as the condition is satisfied.
                return False

        # - - - - DANGER MODE
        self._danger_mode()

        # - - - - SURVIVOR HAS MOVED OUTSIDE THE SURFACE
        self._surface_overrun()

        return False

    def show(self):
        """Displays the Survivor on screen according to
        its status.
        """
        if self.fading or self.immobilized:
            color = self.color_immobilized
        else:
            if self.in_danger:
                color = self.color_danger
            elif self.in_follow and not self.eating:
                color = self.color_follow
            elif self.in_critical and not self.immobilized:
                color = self.color_critical
            elif self.immobilized:
                color = self.color_immobilized
            elif self.eating:
                color = self.color_eating
            elif not self.able_to_eat:
                color = self.color_not_able
            else:
                color = self.color

        if self.eating:
            if self.in_critical:
                bonus_frequency = self.energy_bonus_frequency_critical
            else:
                bonus_frequency = self.energy_bonus_frequency

            if self.timer("eating_oscillation", bonus_frequency):
                pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.survivor_radius_eating)
            else:
                pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.survivor_radius)
        else:
            pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.survivor_radius)

        if SHOW_SENSORIAL_FIELD and not self.immobilized:
            if self.in_danger:
                pygame.draw.circle(screen, self.sensorial_field_color_danger, (int(self.x), int(self.y)),
                                   self.sensorial_radius, 3)

            elif self.in_follow:
                pygame.draw.circle(screen, self.sensorial_field_color_follow, (int(self.x), int(self.y)),
                                   self.sensorial_radius, 3)

            elif self.in_critical:
                pygame.draw.circle(screen, self.sensorial_field_color_critical, (int(self.x), int(self.y)),
                                   self.sensorial_radius, 3)

            else:
                pygame.draw.circle(screen, self.sensorial_field_color, (int(self.x), int(self.y)),
                                   self.sensorial_radius, 1)

    def get_pos(self) -> Vector2:
        """Returns Survivor coordinates.

        Returns:
            tuple: Survivor coordinates.
        """
        pos = self.x, self.y
        return pygame.math.Vector2(pos)

    def __repr__(self):
        return f"Energy : {self.energy}"

# <WORK IN PROGRESS>
class SurvivorsList:
    def __init__(self):
        self.survivors = []

    def __iter__(self):
        self.index = 0
        return self

    def __next__(self):
        if self.index < len(self.survivors):
            survivor = self.survivors[self.index]
            self.index += 1
            return survivor
        else:
            raise StopIteration

    def __len__(self):
        return len(self.survivors)

    def append(self, survivor: Survivor):
        self.survivors.append(survivor)

    def remove(self, survivor: Survivor):
        self.survivors.remove(survivor)
# </WORK IN PROGRESS>