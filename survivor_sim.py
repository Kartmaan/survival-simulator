from pygame_options import pygame, screen, FPS, WIDTH, HEIGHT
from debug import DebugOnScreen
import logging
from utils import np, get_distance, Vector2, format_time, percent
from style import colors
from survivor import Survivor
from danger import Danger
from food import Food

debug_on_screen = DebugOnScreen()
logger = logging.getLogger("debug")

ON_SCREEN_DEBUG = True
NB_OF_SURVIVORS = 200
SHOW_DANGER_DISTANCE_LINE = False
SHOW_FOOD_DISTANCE_LINE = False

nb_of_death = 0

danger_zero = Danger(0, 0)  # Danger model (not displayed)
danger = Danger(np.random.randint(danger_zero.edge*3, WIDTH - danger_zero.edge*3),
                np.random.randint(danger_zero.edge*3, HEIGHT - danger_zero.edge*3))

survivor_zero = Survivor(0, 0)  # Survivor model (not displayed)
survivors: list[Survivor] = []  # Contains all generated Survivor

logger.info(f"Number of survivors : {NB_OF_SURVIVORS}")
logger.info(f"Energy max : {survivor_zero.energy_default}")

# - - - - - - - - - - FOOD CREATION - - - - - - - - - -
# We make sure that the coordinates generated for Food are far enough away from Danger.

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

# - - - - - - - - - - SURVIVORS CREATION - - - - - - - - - -
# We make sure that the coordinates generated for each Survivor are far enough away from Danger and from the edges.
# The distance to Food is not verified, as Survivors are not immediately hungry.
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
        if danger_distance < SURVIVOR.sensorial_radius:
            SURVIVOR.in_danger = True

            danger.attack(SURVIVOR.get_pos())

            # The difference between the Survivor and Danger coordinates is calculated. This gives the horizontal and
            # vertical components of the vector from Danger to Survivor.
            dx = SURVIVOR.pos.x - danger.pos.x
            dy = SURVIVOR.pos.y - danger.pos.y

            # Vector normalization by Pythagorean theorem.
            norm = np.sqrt(dx ** 2 + dy ** 2)
            if norm != 0:
                SURVIVOR.dx = dx / norm
                SURVIVOR.dy = dy / norm

def follow_detection():
    """
    Determines whether a Survivor must follow another Survivor in_danger.

    If a Survivor detects another Survivor in_danger in its sensory field, the latter transmits its escape vector to
    the Survivor so that it takes the same direction.
    """

    # The Survivor will continue its follow as long as the Survivor being followed is in danger.
    for SURVIVOR in survivors:
        SURVIVOR.in_follow = False
        if not SURVIVOR.in_danger:
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

        # - - - - RUSH REGULATOR
        # When the number of eaters is below the maximum (food.max_eaters), and several Survivors are in 'food_rush',
        # each of them rightly considers that Food is not yet full. But when all these Survivors finish their rush,
        # the maximum number of eaters may finally be exceeded. To avoid this, all Survivors in 'food_rush' mode who
        # could cause an excess of eaters are identified, and only one or more of them will be randomly selected so as
        # not to exceed the maximum number of eaters.
        if in_rush > 0:
            # The sum of Survivors eating and those in a rush to eat exceeds food.max_eaters. Regulation is needed.
            if eaters + in_rush > food.max_eaters:
                # Reporting regulation to logger.
                if debug_on_screen.timer("rush_regulation", 0.2):
                    logger.warning(f"Rush regulation : Eaters: {eaters}/{food.max_eaters}, In rush : {in_rush}")

                survivors_in_rush: list[Survivor] = [] # All Survivors in rush mode
                survivors_not_able_to_rush: list[Survivor] = [] # Survivors who won't be able to rush
                nb_of_survivors_able_to_rush = 0
                nb_of_survivors_not_able_to_rush = 0

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
        debug_on_screen.add("Food quantity", f"{food.quantity}/{food.quantity_max}")
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

        # The quantity of Food is at zero and must disappear to reappear elsewhere.
        if food.quantity <= 0:
            # TODO: Cooldown for respawn
            #food.food_timers["time_to_respawn"] = current_time()

            # All Survivors who are eating stop eating, and those in a rush to eat cancel their action.
            for eating_survivor in survivors:
                if eating_survivor.eating or eating_survivor.food_rush:
                    eating_survivor.appetite_suppressant_pill()

            food.find_a_new_place()

            # New Food states provided to all Survivors.
            for not_eating_survivor in survivors:
                not_eating_survivor.food_object = food

def slaughterhouse(survivors_to_remove: list[Survivor]):
    """
    The place where Survivors who must die join their destiny.

    Args:
        survivors_to_remove: list of Survivors to be deleted.
    """
    global nb_of_death

    for poor_survivor in survivors_to_remove:
        survivors.remove(poor_survivor)
        nb_of_death += 1

    # Counting the living and the dead (debug).
    alive = NB_OF_SURVIVORS - nb_of_death
    debug_on_screen.add("Survivors alive", f"{alive}/{NB_OF_SURVIVORS} ({percent(alive, NB_OF_SURVIVORS)}%)")
    debug_on_screen.add("Survivors dead", f"{nb_of_death}/{NB_OF_SURVIVORS} "
                                        f"({percent(nb_of_death, NB_OF_SURVIVORS)}%)")

# - - - - - - - - - - MAIN LOOP - - - - - - - - - -
# The logic of the main loop will essentially consist of a series of iterations on the 'survivors' list for each of
# the main Survivor modes (in_danger, in_follow, ...) in order to check/modify their attributes or activate some of
# their methods.

running = True
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Surface erasing
    # TODO: Change the background color according to the average energy of the Survivors, or according to changing
    #  weather conditions that would have an impact on the attributes of the Survivors and Food?
    screen.fill(colors["BACKGROUND_COLOR"])

    # Pygame options added to debug display.
    debug_on_screen.add("Elapsed time", format_time(pygame.time.get_ticks()))
    debug_on_screen.add("Window size", f"{WIDTH}x{HEIGHT} px")
    debug_on_screen.add("FPS", round(clock.get_fps(), 2))

    # - - - - - - - - - - DANGER DETECTION - - - - - - - - - -
    danger_detection()

    # - - - - - - - - - - FOLLOW DETECTION - - - - - - - - - -
    follow_detection()

    # - - - - - - - - - - FOOD DETECTION - - - - - - - - - -
    food_detection()

    # - - - - - - - - - - MOVE & SHOW SURVIVORS - - - - - - - - - -
    # All Survivor states have been updated, and now it's time to call their move and show methods.

    # Deleting an element from a list during its iteration can lead
    # to unforeseen behavior, so the Survivor to be deleted is stored
    # in this list to avoid deleting it during the iteration of the
    # Survivor list.
    to_remove = []

    # These status variables are used to display the debug.
    in_danger = 0
    in_follow = 0
    in_critical = 0
    energy_list = [0]

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

        # Updating status variables for debugging
        if survivor.in_danger:
            in_danger += 1
        elif survivor.in_follow:
            in_follow += 1
        elif survivor.in_critical:
            in_critical += 1

        # The energy values of each Survivor are inserted in this list so that an average can be displayed in the debug.
        energy_list.append(survivor.energy)

    # Adding infos to the debug
    debug_on_screen.add("In danger", in_danger)
    debug_on_screen.add("In follow", in_follow)
    debug_on_screen.add("In critical", in_critical)
    debug_on_screen.add("Energy mean", round(np.mean(energy_list), 2))
    debug_on_screen.add("Danger rotation speed", f"{danger.rotation_speed}/{danger.rotation_speed_max}")
    debug_on_screen.add("Danger rage", danger.rage)

    # - - - - - - - - - - THE SLAUGHTERHOUSE - - - - - - - - - -
    slaughterhouse(to_remove)

    # - - - - - - - - - - OTHER - - - - - - - - - -
    danger.show()
    food.show()

    if ON_SCREEN_DEBUG:
        debug_on_screen.show()

    pygame.display.flip()  # Updating display
    clock.tick(FPS)  # FPS Limit

pygame.quit()