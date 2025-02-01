import numpy as np

from src.debug import DebugOnScreen
from src.survivor import Survivor
from src.utils import percent

class Watcher:
    """
    Observes and analyzes the overall state of the simulation. It collects information on the environment, entities
    and other relevant aspects, while making this data available to other project modules. This class does not
    directly modify the state of the simulation, but provides an overview and analysis tools. It serves as a
    centralized access point for global information, avoiding the need for global variables.
    """
    def __init__(self):
        self.debug_on_screen: DebugOnScreen
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
            podium_info: list[list] = [] # Info about Survivors on the podium [place, name, energy].

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
                    self.debug_on_screen.add(f"{on_podium[0]}", f"{on_podium[1]}, {on_podium[2]}, "
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
