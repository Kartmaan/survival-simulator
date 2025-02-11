from enum import Enum
from typing import Optional

import numpy as np
import pygame.time

from src.pygame_options import screen
from src.debug import DebugOnScreen
from src.survivor import Survivor
from src.utils import percent, current_time
from src.style import colors

class Watcher:
    """
    Observes and analyzes the overall state of the simulation. It collects information on the environment, entities
    and other relevant aspects, while making this data available to other project modules. This class does not
    directly modify the state of the simulation, but provides an overview and analysis tools. It serves as a
    centralized access point for global information, avoiding the need for global variables.
    """
    def __init__(self):
        self.debug_on_screen: Optional[DebugOnScreen] = None
        self.population: list[Survivor] = []
        self.init_population = 0

        # Stats
        self.living_survivors = 0
        self.dead_survivors = 0
        self.energy_mean = 0
        self.total_in_critical = 0
        self.total_in_danger = 0
        self.total_in_follow = 0
        self.total_eating = 0

        # Podium
        self.min_population_for_podium = 10
        self.places_on_podium = 3
        self.best_survivors: list[Survivor] = []
        self.show_podium = False
        self.we_have_a_winner = False
        self.the_winner: Survivor

    def population_census(self, population: list[Survivor]):
        """
        Census of the Survivors population to extract statistics.

        Args:
            population (list[Survivor]): List of all living Survivors.
        """
        self.living_survivors = len(population)
        self.dead_survivors = self.init_population - self.living_survivors

        energies = []
        critical = 0
        danger = 0
        follow = 0
        eating = 0

        for survivor in population:
            energies.append(survivor.energy)

            if survivor.in_critical:
                critical += 1
            elif survivor.in_danger:
                danger += 1
            elif survivor.in_follow:
                follow += 1
            elif survivor.eating:
                eating += 1

        # Census of the Survivors population to extract statistics.
        if len(energies) > 0:
            self.energy_mean = round(np.mean(energies), 2)
        else:
            self.energy_mean = 0.0

        self.total_in_critical = critical
        self.total_in_danger = danger
        self.total_in_follow = follow
        self.total_eating = eating

        if isinstance(self.debug_on_screen, DebugOnScreen):
            self.debug_on_screen.add("In danger", self.total_in_danger)
            self.debug_on_screen.add("In follow", self.total_in_follow)
            self.debug_on_screen.add("In critical", self.total_in_critical)
            self.debug_on_screen.add("Energy mean", self.energy_mean)

            self.debug_on_screen.add("Survivors alive", f"{self.living_survivors}/{self.init_population} "
                                              f"({percent(self.living_survivors, self.init_population)}%)")

            self.debug_on_screen.add("Survivors dead", f"{self.dead_survivors}/{self.init_population} "
                                                  f"({percent(self.dead_survivors, self.init_population)}%)")

    def podium(self, population: list[Survivor]):
        """
        Highlighting Survivors with the highest energy value, therefore those with the highest probability of survival.

        This highlight consists of a cross drawn on the Survivors on the podium, the cross of the first on the podium
        being wider than the others to better distinguish it. Their names are also displayed to identify them more
        clearly. This is only done if the Survivor population is low enough, so as not to overload the display or
        impact performance.

        Args:
            population (list[Survivor]): List of all living Survivors
        """
        self.threshold_for_podium()

        if len(population) <= 1:
            self.we_have_a_winner = True

        if self.living_survivors > 1 and self.show_podium:
            self.we_have_a_winner = False
            self.best_survivors: list[Survivor] = [] # List containing Survivors with the highest energy value
            podium_info: list[list] = [] # Info about Survivors on the podium [place, name, energy, audacity].

            # Establishing the podium.
            # The Survivor class has a special '__lt__' method based on self.energy, enabling the sorted method to be
            # used on instantiated objects in the class.
            for place, good_survivor in enumerate(sorted(population)[:self.places_on_podium]):
                self.best_survivors.append(good_survivor)
                podium_info.append([place+1, good_survivor.name, good_survivor.energy,
                                    round(good_survivor.audacity, 2)])
                good_survivor.on_podium = True

            self.best_survivors[0].is_first = True # Marking the first

            # The winning Survivor is retrieved so that it can be analyzed and its statistics displayed in the
            # simulation's final floating window.
            self.the_winner = self.best_survivors[0]

            # Search for Survivors who are no longer on the podium or in first place.
            for meh_survivor in population:
                if meh_survivor.on_podium and meh_survivor not in self.best_survivors:
                    meh_survivor.on_podium = False
                if meh_survivor.is_first and meh_survivor != self.best_survivors[0]:
                    meh_survivor.is_first = False

            # On-screen debug display of Survivor information on the podium
            # If the podium spaces are too large, the debug is not displayed to avoid overloading.
            if isinstance(self.debug_on_screen, DebugOnScreen) and len(podium_info) < 5:
                for on_podium in podium_info:
                    # [place, name, energy, audacity]
                    self.debug_on_screen.add(f"{on_podium[0]}", f"{on_podium[1]}, {round(on_podium[2], 2)}, "
                                                                f"{on_podium[3]}")

    def threshold_for_podium(self):
        """
        Checks if the population is small enough to highlight Survivors on the podium.
        """
        if 0 < self.living_survivors <= self.min_population_for_podium:
            self.show_podium = True
        else:
            self.show_podium = False

    # ===================================================================
    #                          GETTERS
    # ===================================================================
    def get_living(self) -> int:
        """
        Returns the number of Survivors still alive.

        Returns:
            int: Number of Survivors alive.
        """
        return self.living_survivors

    def get_dead(self) -> int:
        """
        Returns the number of dead Survivors.

        Returns:
            int: Number of dead Survivors.
        """
        return  self.dead_survivors

    # ===================================================================
    #                          SETTERS
    # ===================================================================
    def set_init_population(self, total_population: int):
        """
        Informs the class of the initial number of Survivors. This method should only be called once, and as early as
        possible in the main file.
        """
        self.init_population = total_population

    def set_debug(self, debug_obj: DebugOnScreen):
        """

        """
        self.debug_on_screen = debug_obj

class Climate(Enum):
    """
    Enumeration of the different climates with, as a value, a list containing :
    - [0]: The average temperature around which to oscillate
    - [1]: Standard deviation
    """
    TEMPERATE = [15.0, 3] # Standard climate (nominal parameters)
    COLD = [-20.0, 5] # Extreme climate (penalized parameters)
    HOT = [55.0, 5] # Extreme climate (penalized parameters)

class Weather:
    """
    Manages weather conditions and their effects on simulation entities.

    This class is responsible for :
    - Managing climate cycles (temperate, cold, hot).
    - Updating temperature according to current climate.
    - Defining climatic effects on entities.
    - The visual transition between climates via a background color fade.
    """
    def __init__(self):
        # -------------------------------------------------------------------
        #                       CLIMATES AND TEMPERATURES
        # -------------------------------------------------------------------
        self.climate_loop: list[Climate] = [Climate.TEMPERATE, Climate.COLD, Climate.TEMPERATE, Climate.HOT]
        self.current_climate_index: int = 0
        self.current_climate: Climate = self.climate_loop[self.current_climate_index]
        self.temperature: float = self.current_climate.value[0]

        # -------------------------------------------------------------------
        #                          TIME MANAGEMENT
        # -------------------------------------------------------------------
        self.weather_timers = {}

        self.fade_start_time = None
        self.fade_duration = 5

        self.temperate_duration = 30
        self.cold_duration = 20
        self.hot_duration = 15
        self.temperature_refresh_frequency = 0.25

        # -------------------------------------------------------------------
        #                              COLORS
        # -------------------------------------------------------------------
        # Climate background colors
        self.current_color = colors["TEMPERATE"]
        self.fade_start_color = None
        self.fade_final_color = None

        self.temperate_color: list[int] = colors["TEMPERATE"]
        self.cold_color: list[int] = colors["COLD"]
        self.hot_color: list[int] = colors["HOT"]

        # -------------------------------------------------------------------
        #                        CLIMATIC PENALTIES
        # -------------------------------------------------------------------
        # Multiplier coefficients for climatic penalties
        # Temperate climates do not incur a penalty.

        # Cold climate penalties
        self.cold_energy_loss = 1.4 # Increased energy consumption
        self.cold_speed = 0.5 # Loss of speed
        self.cold_food_quantity = 0.25 # Less food
        self.cold_food_respawn = 1.8 # Food respawns later
        self.cold_food_decay = 0.1 # Food spoils more slowly (bonus)

        # Hot climate penalties
        self.hot_energy_loss = 1.6 # Increased energy consumption
        self.hot_speed = 0.7 # Loss of speed
        self.hot_food_decay = 3.14 # Food spoils faster
        self.hot_food_quantity = 0.25 # Less food
        self.hot_food_respawn = 2.2 # Food respawns later
        self.hot_rage_cooldown = 0.25 # Danger loses its rage faster (bonus)

        # -------------------------------------------------------------------
        #                              STATUS
        # -------------------------------------------------------------------
        self.fading = False

        # -------------------------------------------------------------------
        #                           OTHER OBJECTS
        # -------------------------------------------------------------------
        self.debug_on_screen: DebugOnScreen

    def timer(self, timer_name: str, duration: float) -> bool:
        """Checks if a timer has expired.

        This allows Weather to have its own timers and therefore to have a personalized time management system
        for each of them.

        Args:
            timer_name (str): Timer name.
            duration (float): Desired duration in seconds.

        Returns:
            bool: True if time is up, False otherwise.
        """
        now = current_time()

        if timer_name not in self.weather_timers:
            self.weather_timers[timer_name] = now
            return False

        elapsed_time = now - self.weather_timers[timer_name]
        if elapsed_time >= duration:
            self.weather_timers[timer_name] = now
            return True

        return False

    def set_climate(self):
        """
        Makes a current climate persist for a set time and switches to the next climate when this time has elapsed.
        """
        # Continuity of temperate climate
        if self.current_climate == Climate.TEMPERATE:
            if self.timer("Temperate", self.temperate_duration):
                # The temperate climate appears twice in the climate loop: the first is followed by the cold climate,
                # the second by the hot climate.
                if self.current_climate_index == 0:
                    self.start_fade(self.temperate_color, self.cold_color)
                else:
                    self.start_fade(self.temperate_color, self.hot_color)

                self.current_climate_index = (self.current_climate_index + 1) % len(self.climate_loop)
                self.current_climate = self.climate_loop[self.current_climate_index]

        # Continuity of cold climate
        elif self.current_climate == Climate.COLD:
            if self.timer("Cold", self.cold_duration):
                self.start_fade(self.cold_color, self.temperate_color)
                self.current_climate_index = (self.current_climate_index + 1) % len(self.climate_loop)
                self.current_climate = self.climate_loop[self.current_climate_index]

        # Continuity of hot climate
        elif self.current_climate == Climate.HOT:
            if self.timer("Hot", self.hot_duration):
                self.start_fade(self.hot_color, self.temperate_color)
                self.current_climate_index = (self.current_climate_index + 1) % len(self.climate_loop)
                self.current_climate = self.climate_loop[self.current_climate_index]

                # Loop restart : resetting timers
                del self.weather_timers["Temperate"]
                del self.weather_timers["Cold"]
                del self.weather_timers["Hot"]

    def set_temperature(self):
        """
        Returns a temperature value centered on a mean and respecting a given standard deviation.

        Repeated calls to the function therefore generate a series of temperature values respecting a normal
        distribution.
        """
        if self.timer("temp_stability", self.temperature_refresh_frequency):
            current_climate = self.current_climate
            mean = current_climate.value[0]
            sd = current_climate.value[1]
            temperature = np.random.normal(mean, sd)

            self.temperature = temperature

    def start_fade(self, start_color: list[int], final_color: list[int]):
        """
        Gives the signal to start a color fade, from one climatic color to the next.

        Args:
            start_color : Color at start of fade
            final_color : Color at end of fade
        """
        self.fade_start_time = pygame.time.get_ticks()
        self.fade_start_color = start_color
        self.fade_final_color = final_color
        self.fading = True

    def fade_background(self):
        """
        Starts background color fading if the climate changes.
        """
        # Between two fades, we keep the state of the last color.
        if self.fade_start_time is None:
            screen.fill(self.current_color)
            return

        # Checks if fading time has elapsed
        elapsed_time = (pygame.time.get_ticks() - self.fade_start_time) / 1000
        t = min(elapsed_time / self.fade_duration, 1.0)

        # Change the RGB values from the starting color to the final color.
        self.current_color = [
            int(self.fade_start_color[0] + t * (self.fade_final_color[0] - self.fade_start_color[0])),
            int(self.fade_start_color[1] + t * (self.fade_final_color[1] - self.fade_start_color[1])),
            int(self.fade_start_color[2] + t * (self.fade_final_color[2] - self.fade_start_color[2]))
        ]

        colors["BACKGROUND_COLOR"] = self.current_color # Used for fading Survivors at the end of their lives.
        screen.fill(self.current_color)

        # End of fading time, all parameters reset.
        if t >= 1.0:
            self.fade_start_time = None
            self.fade_start_color = None
            self.fade_final_color = None
            self.fading = False