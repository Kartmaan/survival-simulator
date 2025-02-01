import logging

import pygame
from pygame.math import Vector2
import numpy as np

from src.pygame_options import screen, WIDTH, HEIGHT
from src.utils import current_time, get_distance
from src.style import colors, draw_cross, draw_square, print_on_screen
from src.food import Food

logger = logging.getLogger("src.debug")

SHOW_SENSORIAL_FIELD = False
SHOW_MEMORY = False
food_zero = Food(0, 0)
names_list = [] # List of all Survivor names to avoid duplication.

class Survivor:
    """
    Entity moving in search of food.

    - The Survivor has a limited amount of energy
    - It moves randomly across the surface, which causes it to lose energy.
    - It has a sensory field that enables it to detect food, danger and other Survivors.
    - When he detects danger, he flees, increasing his speed and losing more energy.
    - When he encounters a Danger, the Survivor establishes a safe distance from it and keeps it for a time.
    - It has an 'audacity' value that determines the length of this safety distance.
    - When it detects another Survivor fleeing, it follows it out of survival instinct.
    - When it detects food and the need arises, it consumes it to increase its energy.
    - A Survivor with a critical energy threshold consumes food more quickly.
    - If a Survivor's energy reaches a critical threshold, its speed is reduced and its sensory field gradually narrows.
    - If energy reaches zero, the Survivor stops and dies.
    - Survivor has a unique name.
    """
    def __init__(self, x, y):
        # -------------------------------------------------------------------
        #                       POSITION / DIRECTION
        # -------------------------------------------------------------------
        self.pos = Vector2(x, y)
        self.x = self.pos.x
        self.y = self.pos.y
        self.dx = 0.0
        self.dy = 0.0

        # -------------------------------------------------------------------
        #                            IDENTITY
        # -------------------------------------------------------------------
        # Attributes that make each Survivor unique.

        self.name = self._give_me_a_name()
        self.audacity_max = 10.0
        self.audacity_min = 1.0
        self.audacity = self._set_audacity()

        # -------------------------------------------------------------------
        #                              SPEED
        # -------------------------------------------------------------------
        self.speed_default = 4
        self.speed = self.speed_default
        self.speed_critical = self.speed / 4
        self.speed_food_rush = self.speed + 1
        self.speed_flee = self.speed + 2
        self.speed_flee_critical = self.speed_critical + 2
        self.speed_showcase = 5

        # -------------------------------------------------------------------
        #                         TIME MANAGEMENT
        # -------------------------------------------------------------------
        # All units in seconds
        self.survivor_timers = {}

        self.direction_duration_min = 2
        self.direction_duration_max = 4

        self.flee_duration_max = 4
        self.flee_duration_min = 0.85
        self.flee_duration = self._set_flee_duration()

        self.deja_vu_flee_duration = 3

        self.fade_duration = 5
        self.immobilization_time = 5

        self.eating_cooldown = 5

        # -------------------------------------------------------------------
        #                             SIZES
        # -------------------------------------------------------------------
        self.survivor_radius_default = 3
        self.survivor_radius = self.survivor_radius_default
        self.survivor_radius_eating = self.survivor_radius + 3 # Oscillation
        self.survivor_radius_showcase = self.survivor_radius_default * 5
        self.sensorial_radius_default = self.survivor_radius * 20
        self.sensorial_radius = self.survivor_radius_default

        # -------------------------------------------------------------------
        #                             COLORS
        # -------------------------------------------------------------------
        self.color = colors["SURVIVOR_NORMAL"]

        # Food
        self.color_eating = colors["SURVIVOR_EATING"]
        self.color_not_able = colors["SURVIVOR_NOT_ABLE"]

        # Danger
        self.color_danger = colors["RED"]
        self.color_follow = colors["SURVIVOR_FOLLOW"]

        # Energy
        self.color_critical = colors["SURVIVOR_CRITICAL"]
        self.color_immobilized = self.color_critical.copy()
        self.final_fading_color = colors["BACKGROUND_COLOR"]

        # Sensorial field
        self.sensorial_field_color = colors["BLACK"]
        self.sensorial_field_color_follow = colors["ORANGE"]
        self.sensorial_field_color_danger = colors["RED"]
        self.sensorial_field_color_critical = colors["BLACK"]

        # -------------------------------------------------------------------
        #                              STATES
        # -------------------------------------------------------------------
        # Food states
        self.food_rush = False
        self.eating = False
        self.able_to_eat = True
        self.hungry = False

        # Danger states
        self.in_danger = False
        self.deja_vu = False # Work in progress
        self.deja_vu_flee = False
        self.in_follow = False

        # Energy states
        self.in_critical = False
        self.immobilized = False
        self.fading = False

        # Podium
        self.on_podium = False
        self.is_first = False

        # -------------------------------------------------------------------
        #                          ENERGY MANAGEMENT
        # -------------------------------------------------------------------
        # The Survivor loses more or less energy as he moves, depending on whether he's in danger or not. Conversely,
        # he gains more or less energy when eating, depending on whether he has a critical energy level or not.

        self.energy_default = 60 # Initial and maximum energy
        self.energy = self.energy_default # Energy value to be handled
        self.energy_hungry = self.energy_default / 1.5 # Energy value at which the Survivor feels the need to eat
        self.energy_critical = self.energy_default / 4 # Energy threshold considered critical
        self.energy_loss_normal = 0.5  # Energy loss in search mode
        self.energy_loss_follow = 1  # Energy loss in follow mode
        self.energy_loss_danger = 1.5  # Energy loss in danger mode
        self.energy_loss_frequency = 1  # Energy loss frequency (in seconds)
        self.energy_bonus_frequency = 0.5  # Frequency of energy gain in search mode (in seconds)
        self.energy_bonus_frequency_critical = 0.25 # Frequency of energy gain in critical mode (in seconds)

        # -------------------------------------------------------------------
        #                         SPATIAL MEMORY
        # -------------------------------------------------------------------
        # When the Survivor encounters a Danger, it remembers its position for a set period of time to avoid coming
        # into contact with it again.

        self.spatial_memory_energy_ratio = 0.25 # Ratio between energy level and memory duration.
        self.spatial_memory_duration = 10 # Memory duration in seconds (will be set on danger_detection)
        self.security_distance_max = screen.width / 6
        self.security_distance = 0

        # -------------------------------------------------------------------
        #                          OBJECT INFOS
        # -------------------------------------------------------------------
        self.food_object: Food = Food(0, 0)
        self.danger_object: None

        # -------------------------------------------------------------------
        #                           STATISTICS
        # -------------------------------------------------------------------
        # TODO : Use these stats for the final winner

        self.nb_of_hits = 0
        self.nb_of_foods_consumed = 0
        self.amount_of_energy_lost = 0
        self.amount_of_energy_recovered = 0

    def _set_audacity(self):
        """
        Sets a random audacity value for Survivor.

        This value will directly influence the setting of the 'security_distance' value.
        """
        audacity_value = np.random.uniform(self.audacity_min, self.audacity_max)
        return audacity_value

    def set_security_distance(self, danger_edge: int):
        """
        Defines a safe distance from the Danger, which the Survivor will try not to cross during his memory time
        (spatial_memory).

        The value of the safety distance is inversely proportional to the value of self.audacity. The lower the
        audacity value, the greater the safe distance, which not only ensures a better chance of survival, but could
        also potentially prevent the Survivor from accessing a food zone.

        Conversely, a higher audacity value will allow the Survivor to risk getting closer to the Danger, giving him
        access to a larger search area for food.

        Args:
            danger_edge (int): Danger edge length. This ensures that the basic safety distance does not overlap with
            Danger.
        """
        relation_scale = 100
        base_distance = danger_edge * 3
        additional_distance = relation_scale / self.audacity
        self.security_distance = base_distance + additional_distance

    def set_spatial_memory_duration(self):
        """
        Defines a period of spatial memory during which the Survivor will try to stay within the safe distance of the
        Danger.

        Memory duration is proportional to the Survivor's energy value: the higher the energy value, the longer the
        memory.
        """
        self.spatial_memory_duration = self.energy * self.spatial_memory_energy_ratio

    def _set_flee_duration(self) -> float:
        """
        Defines a flee duration value according to an audacity value. The higher the audacity value, the shorter the
        flee duration, and vice versa.

        Survivors with the highest audacity values will therefore flee for shorter periods of time, increasing their
        time spent searching for food.
        """
        duration = ((self.audacity_max - self.audacity) / (self.audacity_max - self.audacity_min) *
                    (self.flee_duration_max - self.flee_duration_min) + self.flee_duration_min)
        return duration

    def _give_me_a_name(self):
        """
        Find a name for Survivor avoiding duplicates.
        """
        while True:
            name = self.name_generator()
            if name not in names_list:
                names_list.append(name)
                return name
            else:
                logger.info("Name generator : same name avoided.")
                continue

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
        """Choosing a random direction by randomly change the values of dx and dy. In the 'move' method, the
        Survivor's x and y values are added to dx and dy respectively, which can be between -1 and 1, to establish the
        direction of the next step. The variation in x and y can therefore be positive or negative.
        """
        angle = np.random.uniform(0, 2 * np.pi)
        self.dx = np.cos(angle)
        self.dy = np.sin(angle)

    def _critical_mode(self):
        """
        Defines the Survivor's behavior when its energy reaches a critical threshold.
        """
        # The Survivor has reached a critical energy level, his speed is reduced and his sensory field shrinks.
        if self.energy <= self.energy_critical:
            self.in_critical = True
            self.speed = self.speed_critical
        # Survivor's energy level is high enough.
        else:
            self.in_critical = False
            self.speed = self.speed_default

        # As Survivor's energy level becomes critical, the radius of his sensory field shrinks.
        if self.in_critical and self.sensorial_radius > self.survivor_radius:
            if self.timer("sensorial_radius", 0.5):
                self.sensorial_radius = max(float(self.survivor_radius),
                                            (self.energy / self.energy_critical) * self.sensorial_radius_default)

        elif not self.in_critical:
            self.sensorial_radius = self.sensorial_radius_default

    def _search_mode(self, conditions: list[bool]):
        """
        Defines the Survivor's behavior when it moves randomly in search of food.
        """
        if all(conditions):
            self.x += self.dx * self.speed
            self.y += self.dy * self.speed

            # As the Survivor moves, it loses energy.
            # In order to control the frequency of energy loss, puncture is done in a timer.
            if self.timer("energy_loss", self.energy_loss_frequency):
                if self.in_follow:
                    self.energy -= self.energy_loss_follow
                else:
                    self.energy -= self.energy_loss_normal

            # The change of direction takes place in a timer of random duration, so the Survivor will hold its
            # directions for different lengths of time.
            direction_duration = np.random.uniform(self.direction_duration_min, self.direction_duration_max)
            if self.timer("direction", direction_duration):
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

    def _deja_vu_flee_mode(self):
        """
        Defines the Survivor's behavior when it reaches or exceeds its safe distance with Danger.
        """
        if self.deja_vu_flee:
            self.x += self.dx * self.speed
            self.y += self.dy * self.speed

            # Energy loss
            if self.timer("energy_loss", self.energy_loss_frequency):
               self.energy -= self.energy_loss_normal

            # End of flee
            if self.timer("deja_vu_flee", self.deja_vu_flee_duration):
                self.deja_vu_flee = False

    def _surface_overrun(self):
        """
        Defines the Survivor's behavior when it exceeds the limits of the surface. If the Survivor exits on one side
        of the surface, it exits on the other.
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

    def appetite_suppressant_pill(self):
        """
        Momentarily stops Survivor's attraction to Food.

        Among other things, Survivors 'able_to_eat' state is set to False, which will prevent it from eating again for
        the time defined by 'self.eating_cooldown'. This method also prevents the Survivor from getting stuck in eating
        mode when the amount of Food drops to zero or when Food respawns somewhere else. This is also useful for
        regulating rushes to avoid excess eaters (see 'food_detection' function in main at 'rush regulator' section).
        """
        self.eating = False
        self.food_rush = False
        self.able_to_eat = False

        # Since the 'able_to_eat' state must only remain False for a specified time (via 'self.eating_cooldown'), we
        # create a timestamp here so that the time elapsed since it was created can be checked in Pygame's main loop
        # ('food_detection' function).
        self.survivor_timers["eating_cooldown"] = current_time()

    @staticmethod
    def name_generator(syllables_min=2, syllables_max=4, suffix=False) -> str:
        """
        Generates a name for Survivors by combining syllables.

        Args:
            syllables_min (int): Minimum number of syllables.
            syllables_max (int): Maximum number of syllables.
            suffix (bool, optional): Suffixes is added occasionally. Defaults to False.

        Returns:
            str: The generated name.
        """

        # Basic syllables
        beginning_syllables = ["ba", "be", "bi", "bo", "bu", "da", "de", "di", "do", "du",
                               "fa", "fe", "fi", "fo", "fu", "ga", "ge", "gi", "go", "gu",
                               "ha", "he", "hi", "ho", "hu", "ja", "je", "ji", "jo", "ju",
                               "ka", "ke", "ki", "ko", "ku", "la", "le", "li", "lo", "lu",
                               "ma", "me", "mi", "mo", "mu", "na", "ne", "ni", "no", "nu",
                               "pa", "pe", "pi", "po", "pu", "ra", "re", "ri", "ro", "ru",
                               "sa", "se", "si", "so", "su", "ta", "te", "ti", "to", "tu",
                               "va", "ve", "vi", "vo", "vu", "wa", "we", "wi", "wo", "wu",
                               "ya", "ye", "yi", "yo", "yu", "za", "ze", "zi", "zo", "zu"]

        middle_syllables = ["la", "le", "li", "lo", "lu", "ra", "re", "ri", "ro", "ru",
                            "na", "ne", "ni", "no", "nu", "ma", "me", "mi", "mo", "mu",
                            "ga", "ge", "gi", "go", "gu", "da", "de", "di", "do", "du",
                            "ba", "be", "bi", "bo", "bu"]

        final_syllables = ["ar", "er", "ir", "or", "ur", "al", "el", "il", "ol", "ul",
                           "an", "en", "in", "on", "un", "as", "es", "is", "os", "us",
                           "ard", "erd", "ird", "ord", "urd", "ald", "eld", "ild", "old", "uld",
                           "and", "end", "ind", "ond", "und", "ast", "est", "ist", "ost", "ust"]

        suffixes = ["The Beast", "The Survivor", "The Last", ]

        # Choice of a random number of syllables
        nb_of_syllables = np.random.randint(syllables_min, syllables_max)

        name_parts = []
        final_name = []

        # Building the body of a name with syllables
        for i in range(nb_of_syllables):
            if i == 0:
                name_parts.append(np.random.choice(beginning_syllables))  # beginning syllable
            elif i == nb_of_syllables - 1:
                name_parts.append(np.random.choice(final_syllables))  # middle syllable
            else:
                name_parts.append(np.random.choice(middle_syllables))  # final syllable

        final_name.append("".join(name_parts).capitalize())

        # Add a suffix (optional)
        if suffix and np.random.random() < 0.2:  # proba 20%
            final_name.append(np.random.choice(suffixes))

        # Assembling the parts
        name = " ".join(final_name)

        return name

    def move(self) -> bool:
        """Moves the Survivor in different modes:
            - Search mode: the Survivor moves randomly across the surface in search of food.
            - Rush mode : Survivor perceives food and rushes towards it.
            - Eating mode : The Survivor no longer moves while he recovers energy.
            - Flee mode: the Survivor perceives danger in its sensory field, and flees by increasing its speed.
            - Deja_vu flee mode : Survivor turns back to avoid crossing its security distance with Danger
            - Critical mode: the Survivor has reached a critical energy threshold, and its movement speed decreases.
            - Immobilized mode: Survivor has no energy left and can't move anymore.

            Note: The 'follow' mode isn't defined here by a mode in its own right, since the 'follow_detection'
            function, located in the main Pygame loop, simply momentarily overwrites the Survivor's 'self.dx' and
            'self.dy' values as long as it is in the proximity of a Survivor in danger.

            The method returns Booleans to indicate whether the Survivor should be deleted (True) or not (False).

            Returns:
                bool: Returns True if the Survivor is to be deleted, False otherwise.
        """
        conditions_to_search = [not self.in_danger, not self.eating, not self.food_rush, not self.deja_vu_flee]
        conditions_to_rush = [not self.in_danger, not self.in_follow, not self.immobilized, self.able_to_eat]

        # -------------------------------------------------------------------
        #                       IMMOBILIZATION MODE
        # -------------------------------------------------------------------
        # This phase occurs when the Survivor has run out of energy, and includes
        # immobilization and fading, leading to its deletion.

        # The Survivor has run out of energy but has not yet been immobilized.
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
        # The Survivor is immobilized and its color begins to fade, the last step before it is removed.
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

        # -------------------------------------------------------------------
        #                            MOVEMENT
        # -------------------------------------------------------------------
        # -------------------------------------------------------------------
        #                         CRITICAL MODE
        # -------------------------------------------------------------------
        # Checks if the Survivor has reached a critical energy level. In that case, his speed is reduced and his
        # sensory field shrinks.

        self._critical_mode()

        # -------------------------------------------------------------------
        #                          SEARCH MODE
        # -------------------------------------------------------------------
        # Checks if the Survivor has enough energy to randomly move at normal speed
        # searching for Food.

        self._search_mode(conditions_to_search)

        # -------------------------------------------------------------------
        #                          DEJA VU MODE
        # -------------------------------------------------------------------
        # Checks whether the Survivor is breaking his security distance with Danger

        self._deja_vu_flee_mode()

        if self.deja_vu:
            if self.timer("spatial_memory_duration", self.spatial_memory_duration):
                self.deja_vu = False

        # -------------------------------------------------------------------
        #                        FOOD RUSH MODE
        # -------------------------------------------------------------------
        # Checks if Survivor heads for the food he's detected.

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

        # -------------------------------------------------------------------
        #                          EATING MODE
        # -------------------------------------------------------------------
        # Checks if Survivor stops near food to consume it and recover energy.

        # The rush is over and the Survivor begins to consume the Food.
        if not self.food_rush and self.eating:
            if self.in_critical:
                bonus_frequency = self.energy_bonus_frequency_critical
            else:
                bonus_frequency = self.energy_bonus_frequency

            # The energy bonus occurs at a specific frequency
            if self.timer("energy_bonus", bonus_frequency):
                self.energy += self.food_object.energy_bonus

                # There's still food to eat.
                if self.food_object.quantity > 0:
                    self.food_object.quantity -= self.food_object.energy_bonus
                    self.food_object.adjust_edge()
                # No more food to eat.
                else:
                    #self.food_object.all_survivors = []
                    #self.food_object.find_a_new_place()
                    self.appetite_suppressant_pill()

            # If the Survivor has recovered enough energy, he stops eating. Its 'able_to_eat' state is set False
            # to start the cooldown (in the main loop) determining when it will be able to eat again.
            if self.energy >= self.energy_default:
                self.hungry = False
                self.eating = False
                self.able_to_eat = False
                self.survivor_timers["eating_cooldown"] = current_time()

                # No movement as long as the condition is satisfied.
                return False

        # -------------------------------------------------------------------
        #                           DANGER MODE
        # -------------------------------------------------------------------
        # Checks if the Survivor has encountered danger and must flee

        self._danger_mode()

        # -------------------------------------------------------------------
        #               SURVIVOR HAS MOVED OUTSIDE THE SURFACE
        # -------------------------------------------------------------------
        # Checks if the Survivor has exceeded the limits of the surface.

        self._surface_overrun()

        # The function ends here with or without this return, but it's used to specify that the Survivor isn't to
        # be deleted.
        return False

    def show(self):
        """Displays the Survivor on screen according to its status.
        """

        # Highlights Survivors in deja_vu mode and their security distance radius.
        if self.deja_vu and SHOW_MEMORY:
            if self.deja_vu_flee:
                draw_square(screen, self.get_pos(), self.survivor_radius * 4, (180, 0, 0))
            else:
                draw_square(screen, self.get_pos(), self.survivor_radius * 4)

            pygame.draw.circle(screen, (0,0,0), (int(self.x), int(self.y)),
                               self.security_distance, 2)
            pygame.draw.circle(screen, (250, 0, 0), (int(self.x), int(self.y)),
                               self.sensorial_radius, 2)


        # Highlights Survivors on podium
        if self.on_podium and not self.is_first and not self.fading:
            draw_cross(screen, self.get_pos(), self.survivor_radius+4)
            print_on_screen(screen, pos=self.get_pos() + Vector2(0,10), txt=f"{self.name}", font_size=20)
        elif self.on_podium and self.is_first and not self.fading:
            draw_cross(screen, self.get_pos(), self.survivor_radius + 4, width=3)
            print_on_screen(screen, pos=self.get_pos() + Vector2(0, 10), txt=f"{self.name}", font_size=20)

        # Survivor is immobilized and runs out of energy
        if self.fading or self.immobilized:
            color = self.color_immobilized

        # Setting the color of the Survivor according to its state.
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

        # The Survivor is stopped to consume the food.
        if self.eating:
            # A Survivor at critical energy level eats faster
            if self.in_critical:
                bonus_frequency = self.energy_bonus_frequency_critical
            else:
                bonus_frequency = self.energy_bonus_frequency

            # We oscillate the diameter of its radius at the frequency at which it gains energy.
            if self.timer("eating_oscillation", bonus_frequency):
                pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.survivor_radius_eating)
            else:
                pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.survivor_radius)

        # Survivor drawing
        else:
            pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.survivor_radius)

        # Survivor sensory field display for debugging purposes.
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

    def show_on_showcase(self, surface: pygame.Surface, showcase_side_length: float):
        """
        Shows the winning Survivor in the floating window at the end of the simulation.

        The size of the Survivor is increased to show it more clearly.

        Args:
            surface (Surface) : Surface on witch to draw
            showcase_side_length (float) : Showcase surface side length
        """

        # The Survivor radius is a fraction of the showcase surface side length.
        self.survivor_radius_showcase = showcase_side_length * 0.35
        pygame.draw.circle(surface, colors["GREEN"], (self.x, self.y), self.survivor_radius_showcase)

    def move_on_showcase(self, showcase_side_length: float):
        """
        Simplified version of the 'move' method for moving the winning Survivor within its surface on the final
        simulation window.

        The Survivor moves within a small surface of this window, but instead of crossing the boundaries of the surface,
        as is the case in the 'move' method, the Survivor bounces into it.

        Args:
            showcase_side_length (float) : Showcase surface side length
        """
        self.x += self.dx * self.speed_showcase
        self.y += self.dy * self.speed_showcase

        # As the Survivor moves in a fairly small area, we make sure to have direction durations long enough to cause
        # more bounces on the edges of the surface.
        direction_duration = np.random.uniform(3.5, 4.25)
        if self.timer("direction", direction_duration):
            self._change_direction()

        # Bounces on surface edges
        if self.x - self.survivor_radius_showcase <= 0 or self.x + self.survivor_radius_showcase >= showcase_side_length:
            self.dx *= -1
            self.x = max(self.survivor_radius_showcase,
                         int(min(self.x, showcase_side_length - self.survivor_radius_showcase)))

        if self.y - self.survivor_radius_showcase <= 0 or self.y + self.survivor_radius_showcase >= showcase_side_length:
            self.dy *= -1
            self.y = max(self.survivor_radius_showcase,
                         int(min(self.y, showcase_side_length - self.survivor_radius_showcase)))

    def get_pos(self) -> Vector2:
        """Returns Survivor coordinates.

        Returns:
            tuple: Survivor coordinates.
        """
        pos = self.x, self.y
        return Vector2(pos)

    def __repr__(self) -> str:
        """
        Allows a print to be applied to the instantiated object.
        """
        return f"Name : {self.name}. Energy : {self.energy}"

    def __lt__(self, other) -> bool:
        """
        This special method is used so that the 'sorted' method can be used on a list of Survivor objects.
        """
        return self.energy > other.energy