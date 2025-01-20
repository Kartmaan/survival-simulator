from pygame_options import pygame, screen, FPS, WIDTH, HEIGHT
from utils import random, get_distance, Vector2, format_time, percent, np
from style import colors
from survivor import Survivor
from danger import Danger
from food import Food
from debug import DebugText

debug_display = DebugText()

DEBUG_MODE = True
NB_OF_SURVIVORS = 160
SHOW_DANGER_DISTANCE_LINE = False
SHOW_FOOD_DISTANCE_LINE = False

nb_of_death = 0

danger_zero = Danger(0, 0)  # Danger model (not displayed)
danger = Danger(random.randint(danger_zero.edge, WIDTH - danger_zero.edge), random.randint(50, HEIGHT - 50))

survivor_zero = Survivor(0, 0)  # Survivor model (not displayed)
survivors = []  # Contains all generated Survivor

# - - - - - - - - - - FOOD CREATION - - - - - - - - - -
# We make sure that the coordinates generated for Food are far enough away from Danger.

food_zero = Food(0, 0)  # Food model (not displayed)
food_edge = food_zero.edge
scent_radius = food_zero.scent_field_radius
limit_edge = food_edge + (scent_radius * 2)
min_distance_from_danger = WIDTH / 4

far_enough_from_danger = False
while not far_enough_from_danger:
    x = random.randint(limit_edge, WIDTH - limit_edge)
    y = random.randint(limit_edge, HEIGHT - limit_edge)
    distance = get_distance(Vector2(x, y), danger.get_pos())
    if distance < min_distance_from_danger:
        continue
    else:
        far_enough_from_danger = True

food = Food(x, y)

# - - - - - - - - - - SURVIVORS CREATION - - - - - - - - - -
# We make sure that the coordinates generated for each Survivor are far enough away from Danger and Food.

for _ in range(NB_OF_SURVIVORS):
    radius = survivor_zero.sensorial_radius
    limit_edge = survivor_zero.sensorial_radius
    min_distance_from_danger = radius + danger.edge
    min_distance_from_food = radius + food.scent_field_radius

    # The Survivor's coordinates are generated in such a way that the
    # Danger isn't in his sensory field and so that it's not too close
    # to the edge of the surface.
    far_enough_from_danger_and_food = False
    while not far_enough_from_danger_and_food:
        x = random.randint(limit_edge, WIDTH - limit_edge)
        y = random.randint(limit_edge, HEIGHT - limit_edge)

        distance_from_danger = get_distance(Vector2(x, y), danger.get_pos())
        distance_from_food = get_distance(Vector2(x, y), food.get_pos())

        if distance_from_danger <= min_distance_from_danger and distance_from_food <= min_distance_from_food:
            # print("TOO CLOSE AVOIDED")
            continue
        else:
            far_enough_from_danger_and_food = True

    survivor = Survivor(x, y)
    survivors.append(survivor)

# - - - - - - - - - - MAIN LOOP - - - - - - - - - -
running = True
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Surface erasing
    screen.fill(colors["BACKGROUND_COLOR"])

    debug_display.add("Elapsed time", format_time(pygame.time.get_ticks()))
    debug_display.add("Window size", f"{WIDTH}x{HEIGHT} px")
    debug_display.add("FPS", round(clock.get_fps(), 2))

    # - - - - - - - - - - DANGER DETECTION - - - - - - - - - -
    food.danger_object = danger

    for survivor in survivors:
        # print(survivor.energy, end="\r")

        # Recovering the distance between Survivor and Danger
        danger_distance = get_distance(survivor.get_pos(), danger.get_pos())

        # Danger is in the area of Survivor's sensory field.
        # Survivor enters 'in_danger' mode and an escape
        # vector is generated.

        if danger.attacking or danger.returning:
            danger.attack(survivor.get_pos())

        if danger_distance - (danger.edge / 2) < survivor.sensorial_radius:
            survivor.in_danger = True

            danger.attack(survivor.get_pos())

            # The difference between the Survivor and
            # Danger coordinates is calculated. This
            # gives the horizontal and vertical components
            # of the vector from Danger to Survivor.
            dx = survivor.pos.x - danger.pos.x
            dy = survivor.pos.y - danger.pos.y

            # Vector normalization by Pythagorean theorem.
            norm = np.sqrt(dx ** 2 + dy ** 2)
            if norm != 0:
                survivor.dx = dx / norm
                survivor.dy = dy / norm

    # - - - - - - - - - - FOLLOW DETECTION - - - - - - - - - -
    # If a Survivor encounters another Survivor in danger within its sensory field, it follows it as it flees.
    for survivor in survivors:
        survivor.in_follow = False
        if not survivor.in_danger:
            for other_survivor in survivors:
                if other_survivor != survivor and other_survivor.in_danger:
                    if (get_distance(survivor.get_pos(), other_survivor.get_pos()) <
                            (survivor.sensorial_radius + other_survivor.sensorial_radius)):
                        survivor.in_follow = True
                        survivor.dx = other_survivor.dx
                        survivor.dy = other_survivor.dy
                        break  # Another Survivor in danger

    # - - - - - - - - - - FOOD DETECTION - - - - - - - - - -
    # A Survivor can only detect Food if :
    # - its energy level is less than or equal to its 'energy_hungry' threshold
    # - it's not in danger
    # - it's not following a Survivor in danger
    # - it's not already in 'food_rush' mode
    # - it's not in 'eating' mode
    # - it's able to eat (not in eating_cooldown)
    # - it's not immobilized
    # - Food isn't full

    for survivor in survivors:
        conditions_to_detect_food = [survivor.energy <= survivor.energy_hungry, not survivor.in_danger,
                                     not survivor.in_follow, not survivor.food_rush, not survivor.eating,
                                     survivor.able_to_eat, not survivor.immobilized, not food.full]

        # A Survivor has a cooldown before being able to eat again, and here we check whether it has expired.
        if not survivor.able_to_eat:
            if survivor.timer("eating_cooldown", survivor.eating_cooldown):
                survivor.able_to_eat = True

        # To check whether the maximum number of Survivors who can simultaneously eat the Food has been reached, we go
        # through the list of Survivors and count those whose 'eating' and 'food_rush' status is True.
        eaters = 0
        in_rush = 0
        for poor_survivor in survivors:
            if poor_survivor.eating:
                eaters += 1
            if poor_survivor.food_rush:
                in_rush += 1

        debug_display.add("Eaters", eaters)
        debug_display.add("Food full", food.full)
        debug_display.add("Food quantity", food.quantity)
        debug_display.add("Food edge", food.edge)
        debug_display.add("Food radius", food.scent_field_radius)

        if eaters >= food.max_eaters or in_rush >= food.max_eaters:
            food.full = True
        else:
            food.full = False

        distance = get_distance(survivor.get_pos(), food.get_pos())

        if all(conditions_to_detect_food):
            #survivor.food_object = food
            # If the Survivor's sensory field overlaps the Food's olfactory field, then the Survivor has detected
            # the Food. Its 'food_rush' mode is activated to send a signal to the 'move' method so that the Survivor
            # moves in the direction of the Food.
            # TODO : If the Survivor activates the 'food_rush' mode when it is at a distance less than the
            #  'eater_radius', its rush movement must be in the opposite direction.
            if distance < food.scent_field_radius + survivor.sensorial_radius:
                survivor.food_rush = True

                # We send some information to Survivor about Food.
                survivor.food_pos = food.get_pos()
                survivor.food_field_radius = food.scent_field_radius
                survivor.food_bonus = food.energy_bonus
                survivor.food_object = food

            # No detection, no rush
            else:
                survivor.food_rush = False

    # - - - - - - - - - - MOVE & SHOW SURVIVORS - - - - - - - - - -

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
    debug_display.add("In danger", in_danger)
    debug_display.add("In follow", in_follow)
    debug_display.add("In critical", in_critical)
    debug_display.add("Energy mean", round(np.mean(energy_list), 2))
    debug_display.add("Danger rotation speed", f"{danger.rotation_speed}/{danger.rotation_speed_max}")
    debug_display.add("Danger rage", danger.rage)

    # - - - - - - - - - - THE REAPER ROOM - - - - - - - - - -
    # Survivors deletion
    for survivor in to_remove:
        survivors.remove(survivor)
        nb_of_death += 1

    # Counting the living and the dead (debug).
    alive = NB_OF_SURVIVORS - nb_of_death
    debug_display.add("Survivors alive", f"{alive}/{NB_OF_SURVIVORS} ({percent(alive, NB_OF_SURVIVORS)}%)")
    debug_display.add("Survivors dead", f"{nb_of_death}/{NB_OF_SURVIVORS} "
                                        f"({percent(nb_of_death, NB_OF_SURVIVORS)}%)")
    # - - - - - - - - - - OTHER - - - - - - - - - -
    danger.show()
    food.show()

    if DEBUG_MODE:
        debug_display.show()

    pygame.display.flip()  # Updating display
    clock.tick(FPS)  # FPS Limit

pygame.quit()