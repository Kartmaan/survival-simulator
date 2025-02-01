import logging

import pygame
from pygame.math import Vector2
import numpy as np

from src.pygame_options import screen, FPS, WIDTH, HEIGHT
from src.debug import DebugOnScreen
from src.utils import current_time, get_distance, format_time
from src.style import colors
from src.survivor import Survivor
from src.danger import Danger
from src.food import Food
from src.world import Watcher
from src.interface import show_winner_window

# ===================================================================
#                          INITIALIZATION
# ===================================================================
watcher = Watcher()
debug_on_screen = DebugOnScreen()
logger = logging.getLogger("src.debug")

# Displaying information useful for debugging
ON_SCREEN_DEBUG = False
SHOW_DANGER_DISTANCE_LINE = False
SHOW_FOOD_DISTANCE_LINE = False

# Number of Survivors to generate
NB_OF_SURVIVORS = 180

watcher.set_init_population(NB_OF_SURVIVORS)
watcher.set_debug(debug_on_screen)

survivor_zero = Survivor(0, 0)  # Survivor model (not displayed)
survivors: list[Survivor] = []  # Contains all generated Survivor

logger.info(f"Number of survivors : {NB_OF_SURVIVORS}")
logger.info(f"Energy max : {survivor_zero.energy_default}")

# ===================================================================
#                          DANGER CREATION
# ===================================================================
# The Danger is placed first, as its position will determine that of
# Food. We make sure it's far enough from the edges of the surface so
# that its attack animations are visible.

danger_zero = Danger(0, 0)  # Danger model (not displayed)
danger = Danger(np.random.randint(danger_zero.edge*3, WIDTH - danger_zero.edge*3),
                np.random.randint(danger_zero.edge*3, HEIGHT - danger_zero.edge*3))

# ===================================================================
#                          FOOD CREATION
# ===================================================================
# We make sure that the coordinates generated for Food are far enough
# away from Danger.

food_zero = Food(0, 0)  # Food model (not displayed)
food_edge = food_zero.edge
scent_radius = food_zero.scent_field_radius
limit_edge = food_edge + (scent_radius * 2)
min_distance_from_danger = WIDTH / 4

# Naive attempt
x = np.random.randint(int(limit_edge), int(WIDTH - limit_edge))
y = np.random.randint(int(limit_edge), int(HEIGHT - limit_edge))

distance = get_distance(Vector2(x, y), danger.get_pos())
far_enough_from_danger = False

if distance < min_distance_from_danger:
    while not far_enough_from_danger:
        x = np.random.randint(limit_edge, WIDTH - limit_edge)
        y = np.random.randint(limit_edge, HEIGHT - limit_edge)
        distance = get_distance(Vector2(x, y), danger.get_pos())
        if distance < min_distance_from_danger:
            logger.warning("Food generation : Food too close from Danger avoided")
            continue
        else:
            far_enough_from_danger = True

food = Food(x, y)
# ===================================================================
#                        SURVIVORS GENERATION
# ===================================================================
# We make sure that the coordinates generated for each Survivor are far
# enough away from Danger and from the edges. The distance to Food is not
# verified, as Survivors are not immediately hungry.

for _ in range(NB_OF_SURVIVORS):
    survivor_sensorial_radius = survivor_zero.sensorial_radius
    limit_edge = survivor_zero.sensorial_radius * 1.5
    min_distance_from_danger = survivor_sensorial_radius + danger.edge * 4

    # Naive attempt
    x = np.random.randint(limit_edge, WIDTH - limit_edge)
    y = np.random.randint(limit_edge, HEIGHT - limit_edge)

    distance_from_danger = get_distance(Vector2(x, y), danger.get_pos())
    far_enough_from_danger = False

    if distance_from_danger < min_distance_from_danger:
        while not far_enough_from_danger:
            x = np.random.randint(limit_edge, WIDTH - limit_edge)
            y = np.random.randint(limit_edge, HEIGHT - limit_edge)

            distance_from_danger = get_distance(Vector2(x, y), danger.get_pos())

            if distance_from_danger <= min_distance_from_danger:
                logger.warning("Survivors generation : Survivor too close from danger avoided")
                continue
            else:
                far_enough_from_danger = True

    survivor = Survivor(x, y)
    survivors.append(survivor)

# ===================================================================
#                          FUNCTIONS
# ===================================================================
# Useful functions for detecting certain events.

def danger_detection():
    """
    Defines the conditions for a Survivor to detect a Danger.
    """
    # We send the Danger object to Food so that it can know its position at all times, which will be useful for
    # ensuring that Food's respawn takes place at a reasonable distance from Danger.
    food.danger_object = danger

    for SURVIVOR in survivors:
        # Recovering the distance between Survivor and Danger
        danger_distance = get_distance(SURVIVOR.get_pos(), danger.get_pos())

        # Danger is still in attack/return animation
        if danger.attacking or danger.returning:
            danger.attack(SURVIVOR.get_pos())

        # Danger is in the area of Survivor's sensory field. Survivor enters 'in_danger' mode and an escape vector
        # is generated. -- - (danger.edge / 2)
        if danger_distance < SURVIVOR.sensorial_radius and not SURVIVOR.immobilized:
            SURVIVOR.in_danger = True
            SURVIVOR.nb_of_hits += 1

            # The Survivor establishes a safe distance between himself and the Danger, which he will try not to cross
            # for the duration of his spatial memory.
            SURVIVOR.set_security_distance(danger.edge)
            SURVIVOR.set_spatial_memory_duration()
            SURVIVOR.deja_vu = True
            SURVIVOR.survivor_timers["spatial_memory"] = current_time() # Time referential

            # Danger launches his attack on Survivor
            danger.attack(SURVIVOR.get_pos()) #

            # The difference between the Survivor and Danger coordinates is calculated. This gives the horizontal and
            # vertical components of the vector from Danger to Survivor.
            dx = SURVIVOR.pos.x - danger.pos.x
            dy = SURVIVOR.pos.y - danger.pos.y

            # Vector normalization by Pythagorean theorem.
            norm = np.sqrt(dx ** 2 + dy ** 2)
            if norm != 0:
                SURVIVOR.dx = dx / norm
                SURVIVOR.dy = dy / norm

def deja_vu_detection():
    """
    When a Survivor is attacked by a Danger, it flees, keeping in mind a security distance around it so as not to cross
    it again for a set time. This time is marked by the activation of the Survivor's 'self.deja_vu' state. This
    function checks whether a Survivor in 'deja_vu' mode reaches or exceeds this security distance. If so, the Survivor
    turns back.
    """
    for SURVIVOR in survivors:
        if not SURVIVOR.in_danger and not SURVIVOR.deja_vu_flee and SURVIVOR.deja_vu:
            if get_distance(SURVIVOR.get_pos(), danger.get_pos()) < SURVIVOR.security_distance + danger.edge:
                SURVIVOR.deja_vu_flee = True

                SURVIVOR.dx = -SURVIVOR.dx
                SURVIVOR.dy = -SURVIVOR.dy

def follow_detection():
    """
    Determines whether a Survivor must follow another Survivor in_danger.

    If a Survivor detects another Survivor in_danger in its sensory field, the latter transmits its escape vector to
    the Survivor so that it takes the same direction. When the Survivor is in 'search' mode, this function simply
    momentarily overwrites the Survivor's 'self.dx' and 'self.dy' values as long as the Survivor is close to a Survivor
    in danger. It is therefore not a movement mode in its own right, like those defined in Survivor's 'move' method,
    but a succession of punctual adjustments.
    """

    # The Survivor will continue its follow as long as the Survivor being followed is in danger.
    # Survivors in 'deja_vu' mode still remember the location of the Danger, having already encountered it, so they
    # don't follow the escape of the Survivor in Danger.
    for SURVIVOR in survivors:
        SURVIVOR.in_follow = False
        if not SURVIVOR.in_danger and not SURVIVOR.deja_vu:
            for other_survivor in survivors:
                if other_survivor != SURVIVOR and other_survivor.in_danger:
                    if (get_distance(SURVIVOR.get_pos(), other_survivor.get_pos()) <
                            (SURVIVOR.sensorial_radius + other_survivor.sensorial_radius)):
                        SURVIVOR.in_follow = True
                        # The Survivor in_danger transmits his escape vector to the other Survivors in his sensory
                        # field.
                        SURVIVOR.dx = other_survivor.dx
                        SURVIVOR.dy = other_survivor.dy
                        break  # Another Survivor in danger ?

def food_detection():
    """
    Determines whether the Survivor has detected the Food and is authorized to begin his rush towards it.

    Several conditions must be met for a Survivor to detect Food :
    - its energy level is less than or equal to its 'energy_hungry' threshold
    - it's not in danger
    - it's not following a Survivor in danger
    - it's not already in 'food_rush' mode
    - it's not in 'eating' mode
    - it's able to eat (not in eating_cooldown)
    - it's not immobilized
    - Food isn't full
    - Will not be a surplus eater on Food (see Rush Regulator section)
    """
    for SURVIVOR in survivors:
        conditions_to_detect_food = [SURVIVOR.energy <= SURVIVOR.energy_hungry, not SURVIVOR.in_danger,
                                     not SURVIVOR.in_follow, not SURVIVOR.food_rush, not SURVIVOR.eating,
                                     SURVIVOR.able_to_eat, not SURVIVOR.immobilized, not food.full]

        # A Survivor has a cooldown before being able to eat again, and here we check whether it has expired.
        if not SURVIVOR.able_to_eat:
            if SURVIVOR.timer("eating_cooldown", SURVIVOR.eating_cooldown):
                SURVIVOR.able_to_eat = True

        # To check whether the maximum number of Survivors who can simultaneously eat the Food has been reached, we go
        # through the list of Survivors and count those whose 'eating' and 'food_rush' status is True.
        eaters = 0
        in_rush = 0
        for hungry_survivor in survivors:
            if hungry_survivor.eating:
                eaters += 1
            if hungry_survivor.food_rush:
                in_rush += 1

        # Food becomes full if the maximum number of eaters is reached
        if eaters >= food.max_eaters or in_rush >= food.max_eaters:
            food.full = True
        else:
            food.full = False

        # -------------------------------------------------------------------
        #                         RUSH REGULATOR
        # -------------------------------------------------------------------
        # When the number of eaters is below the maximum (food.max_eaters), and
        # several Survivors are in 'food_rush', each of them rightly considers
        # that Food is not yet full. But when all these Survivors finish their
        # rush, the maximum number of eaters may finally be exceeded. To avoid
        # this, all Survivors in 'food_rush' mode who could cause an excess of
        # eaters are identified, and only one or more of them will be randomly
        # selected so as not to exceed the maximum number of eaters.

        if in_rush > 0:
            # The sum of Survivors eating and those in a rush to eat exceeds food.max_eaters. Regulation is needed.
            if eaters + in_rush > food.max_eaters:
                # Reporting regulation to logger.
                if debug_on_screen.timer("rush_regulator", 0.2):
                    logger.info(f"Rush regulation : Eaters: {eaters}/{food.max_eaters}, In rush : {in_rush}")

                survivors_in_rush: list[Survivor] = [] # All Survivors in rush mode
                #survivors_not_able_to_rush: list[Survivor] = [] # Survivors who won't be able to rush
                #nb_of_survivors_able_to_rush = 0
                #nb_of_survivors_not_able_to_rush = 0

                # Identifying Survivors in rush.
                for rushing_survivor in survivors:
                    if rushing_survivor.food_rush:
                        survivors_in_rush.append(rushing_survivor)

                # There's still room to eat
                if eaters < food.max_eaters:
                    # Calculating the number of Survivors still able to join the feast.
                    nb_of_survivors_able_to_rush = food.max_eaters - eaters

                    # There are more Survivors in rush mode than there are places to eat.
                    if len(survivors_in_rush) > nb_of_survivors_able_to_rush:
                        # Calculating the number of Survivors who will not be able to rush
                        nb_of_survivors_not_able_to_rush = len(survivors_in_rush) - nb_of_survivors_able_to_rush

                        # Among the Survivors currently in rush, we randomly select those who will not be able to rush.
                        # These randomly selected Survivors are contained in a dedicated list.
                        survivors_not_able_to_rush = np.random.choice(survivors_in_rush,
                                                                      nb_of_survivors_not_able_to_rush, replace=False)

                        # The 'appetite_suppressant_pill' method of the designated Survivors is called, which, among
                        # other things, sets their 'able_to_eat' status to False, a discriminating factor for detecting
                        # Food.
                        for unlucky_survivor in survivors_not_able_to_rush:
                            unlucky_survivor.appetite_suppressant_pill()

        # Notify the logger if the maximum number of eaters is exceeded.
        if eaters > food.max_eaters:
            if debug_on_screen.timer("eaters_exceeding", 2):
                logger.critical(f"Max eaters exceeding : {eaters}/{food.max_eaters}")

        # Adding Food information to the debug
        debug_on_screen.add("Eaters", eaters)
        debug_on_screen.add("Food full", food.full)
        debug_on_screen.add("Food quantity", f"{food.quantity}/{food.init_quantity}")
        debug_on_screen.add("Food edge", f"{round(food.edge, 2)}/{food.edge_max}")
        debug_on_screen.add("Food radius", f"{round(food.scent_field_radius, 2)}/"
                                           f"{food.scent_field_radius_max}")

        dist = get_distance(SURVIVOR.get_pos(), food.get_pos())

        if all(conditions_to_detect_food):
            # If the Survivor's sensory field overlaps the Food's olfactory field, then the Survivor has detected
            # the Food. Its 'food_rush' mode is activated to send a signal to the 'move' method so that the Survivor
            # moves in the direction of the Food.
            if dist < food.scent_field_radius + SURVIVOR.sensorial_radius:
                SURVIVOR.food_rush = True

                # We send some information to Survivor about Food.
                SURVIVOR.food_pos = food.get_pos()
                SURVIVOR.food_field_radius = food.scent_field_radius
                SURVIVOR.food_bonus = food.energy_bonus
                SURVIVOR.food_object = food

            # No detection, no rush.
            else:
                SURVIVOR.food_rush = False

def slaughterhouse(survivors_to_remove: list[Survivor]):
    """
    The place where Survivors who must die join their destiny.
    This is also where the living and the dead are counted.

    Args:
        survivors_to_remove: list of Survivors to be deleted.
    """

    for poor_survivor in survivors_to_remove:
        survivors.remove(poor_survivor)

# ===================================================================
#                             MAIN LOOP
# ===================================================================
# The logic of the main loop will essentially consist of a series of iterations on the 'survivors' list for each of
# the main Survivor modes (in_danger, in_follow, ...) in order to check/modify their attributes or activate some of
# their methods.

running = True
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            logger.info(f"Simulation duration : {format_time(pygame.time.get_ticks())}")
            running = False

    # Surface erasing
    # TODO: Change the background color according to the average energy of the Survivors, or according to changing
    #  weather conditions that would have an impact on the attributes of the Survivors and Food ?
    screen.fill(colors["BACKGROUND_COLOR"])

    # Pygame options added to debug display.
    debug_on_screen.add("Elapsed time", format_time(pygame.time.get_ticks()))
    debug_on_screen.add("Window size", f"{WIDTH}x{HEIGHT} px")
    debug_on_screen.add("FPS", round(clock.get_fps(), 2))

    # -------------------------------------------------------------------
    #                        DANGER DETECTION
    # -------------------------------------------------------------------
    # Checks if Survivor is in danger

    danger_detection()

    debug_on_screen.add("Danger rotation speed", f"{danger.rotation_speed}/{danger.rotation_speed_max}")
    debug_on_screen.add("Danger rage", danger.rage)

    # -------------------------------------------------------------------
    #                        FOLLOW DETECTION
    # -------------------------------------------------------------------
    # Checks if Survivor must follow another Survivor in danger

    follow_detection()

    # -------------------------------------------------------------------
    #                        FOOD DETECTION
    # -------------------------------------------------------------------
    # Checks if Survivor has detected Food and if the Food has been consumed

    food_detection()
    food.checker(survivors)

    # -------------------------------------------------------------------
    #                        DEJA VU DETECTION
    # -------------------------------------------------------------------
    # Checks if Survivor in 'deja_vu' mode has reached his security distance
    # from Danger.

    deja_vu_detection()

    # -------------------------------------------------------------------
    #                      MOVE & SHOW SURVIVORS
    # -------------------------------------------------------------------
    # All Survivor states have been updated, and now it's time to call their
    # move and show methods.

    # Deleting an element from a list during its iteration can lead
    # to unforeseen behavior, so the Survivor to be deleted is stored
    # in this list to avoid deleting it during the iteration of the
    # Survivor list.
    to_remove = []

    for survivor in survivors:
        # If the method returns True, the Survivor must be deleted.
        should_remove = survivor.move()

        if not should_remove:
            survivor.show()
        else:
            to_remove.append(survivor)

        # Display the lines separating each survivor from Danger and Food (for debugging purposes).
        if SHOW_DANGER_DISTANCE_LINE:
            pygame.draw.line(screen, (255, 0, 0), survivor.get_pos(), danger.get_pos())
        if SHOW_FOOD_DISTANCE_LINE:
            pygame.draw.line(screen, (0, 0, 255), survivor.get_pos(), food.get_pos())

    # -------------------------------------------------------------------
    #                      THE SLAUGHTERHOUSE
    # -------------------------------------------------------------------
    # Survivors running out of energy are removed

    slaughterhouse(to_remove)

    # -------------------------------------------------------------------
    #                      POPULATION CENSUS
    # -------------------------------------------------------------------
    # A census of the Survivors population to produce useful statistics
    # (such as the number of living and dead Survivors, etc.).

    watcher.population_census(survivors)

    # -------------------------------------------------------------------
    #                          THE PODIUM
    # -------------------------------------------------------------------
    # Establishing the podium to highlight the Survivors with the highest
    # energy value. This is only displayed once the population has fallen
    # enough.

    watcher.podium(survivors)
    # -------------------------------------------------------------------
    #                             OTHER
    # -------------------------------------------------------------------
    if not watcher.we_have_a_winner:
        danger.show()
        food.show()

    else:
        if len(survivors) > 0:
            survivors.clear()
            #watcher.the_winner.pos = Vector2(1,1)
            #watcher.the_winner.x = watcher.the_winner.pos.x
            #watcher.the_winner.y = watcher.the_winner.pos.y

        show_winner_window(watcher.the_winner)

    if ON_SCREEN_DEBUG:
        debug_on_screen.show()

    pygame.display.flip()  # Updating display
    clock.tick(FPS)  # FPS Limit

pygame.quit()