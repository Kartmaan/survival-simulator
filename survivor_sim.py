import pygame
import random
import numpy as np

# Initialisation de Pygame
pygame.init()

# Screen options
WIDTH, HEIGHT = 1024, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Survivors sim")

FPS = 30

# Colors
WHITE = [255, 255, 255]
BLACK = [45, 45, 45]
RED = [200, 0, 0]
GREEN = [0, 200, 0]
BLUE = [0, 0, 255]
ORANGE = [255, 165, 0]

NB_OF_SURVIVORS = 50
SHOW_SENSORIAL_FIELD = False
SHOW_DISTANCE_LINE = False

def get_distance(p1: tuple, p2: tuple) -> float:
  """Returns the Euclidean distance between two coordinates.

  Args:
  p1 : First coordinates
  p2 : Second coordinates

  Returns:
  The distance between the two coordinates 
  """
  #distance = np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
  distance = np.linalg.norm(np.array(p2) - np.array(p1))
  return distance

def current_time() -> float:
    """Returns the number of seconds since Pygame was 
    initialized.

    Pygame's get_ticks method returns a value in 
    milliseconds, which is divided by 1000 to obtain 
    seconds.

    Returns:
        float: Number of seconds since initialization.
    """    
    return pygame.time.get_ticks() / 1000.0

class Survivor:
    def __init__(self, x, y):
        # Position / Direction
        self.x = x
        self.y = y
        self.dx = 0.0
        self.dy = 0.0

        # Speed
        self.speed_default = 4
        self.speed = self.speed_default
        self.speed_critical = self.speed / 4
        self.speed_flee = self.speed + 2
        self.speed_flee_critical = self.speed_critical + 2

        # Time management
        self.survivor_timers = {}
        self.direction_duration_min = 2
        self.direction_duration_max = 7
        self.flee_duration = 3
        self.fade_duration = 5
        self.immobilization_time = 5

        # Size
        self.survivor_radius_default = 5
        self.survivor_radius = self.survivor_radius_default
        self.sensorial_radius_default = self.survivor_radius * 5
        self.sensorial_radius = self.survivor_radius_default

        # Colors
        self.color = GREEN
        self.color_danger = RED
        self.color_follow = ORANGE
        self.color_critical = BLACK
        self.color_immobilized = self.color_critical.copy()
        self.final_fading_color = WHITE
        self.sensorial_field_color = GREEN
        self.sensorial_field_color_follow = ORANGE
        self.sensorial_field_color_danger = RED
        self.sensorial_field_color_critical = BLACK
        
        # States
        self.in_danger = False
        self.in_follow = False
        self.in_critical = False
        self.immobilized = False
        self.fading = False

        # Energy management
        self.energy_default = 25
        self.energy = self.energy_default
        self.energy_critical = self.energy_default / 4
        self.energy_loss_frequency = 1 # In second
        self.energy_loss_normal = 0.5 # Per second
        self.energy_loss_follow = 1 # Per second
        self.energy_loss_danger = 1.5 # Per second

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
        # Otherwise the function returns False.
        elapsed_time = now - self.survivor_timers[timer_name]
        if elapsed_time >= duration:
            self.survivor_timers[timer_name] = now
            return True

        return False

    def change_direction(self):
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
    
    def move(self) -> bool:
        """Moves the Survivor in different modes:
            - Search mode: the Survivor moves randomly 
            across the surface in search of food.
            - Escape mode: the Survivor perceives danger 
            in its sensory field, and flees by increasing 
            its speed.
            - Critical mode: The Survivor has reached a 
            critical energy threshold, and its movement 
            speed decreases.
            - Immobilized mode: Survivor has no energy 
            left and can't move anymore.

            Returns:
                bool: Returns True if the Survivor is to 
                be deleted, False otherwise.
        """
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
            #print(f"elapsed_fade_time: {elapsed_fade_time}, fade_progress: {fade_progress}")

            # When the ratio is 1, this means that the time allocated 
            # to fading has elapsed, but depending on the FPS value, 
            # it's possible that the step between each loop passage 
            # is too large, so that “fade_progress” never reaches 1. 
            # To compensate for this, we add a tolerance value.
            # If the condition is True, the function stops by 
            # returning True, which will send a signal (in the main 
            # loop) to delete the Survivor.
            TOLERANCE = 1e-2
            if fade_progress >= 1 - TOLERANCE:
                #print("FADING OVER")
                #self.immobilized = False
                #self.fading = False
                return True # Survivor will be deleted (main loop)

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

        # - - - - - - - - - - MOUVEMENT - - - - - - - - - -

        # - - - - CRITICAL MODE

        # The Survivor's energy has reached a critical threshold, 
        # and its speed mode changes.
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
                self.sensorial_radius = max(self.survivor_radius, (self.energy / self.energy_critical) * self.sensorial_radius_default)
        
        elif not self.in_critical:
            self.sensorial_radius = self.sensorial_radius_default
        
        # - - - - NORMAL MODE

        # The Survivor is in no danger and moves randomly.
        if not self.in_danger:
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
            if self.timer("direction", random.uniform(self.direction_duration_min, self.direction_duration_max)):
                self.change_direction()

        # - - - - DANGER MODE

        # Survivor is in danger and flees
        else:
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

        # - - - - SURVIVOR HAS MOVED OUTSIDE THE SURFACE

        # If the Survivor goes out on one side of the 
        # surface, it comes back in on the other.
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
            elif self.in_follow:
                color = self.color_follow
            elif self.in_critical and not self.immobilized:
                color = self.color_critical
            elif self.immobilized:
                color = self.color_immobilized
            else:
                color = self.color

        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), self.survivor_radius)
        
        if SHOW_SENSORIAL_FIELD and not self.immobilized:
            if self.in_danger:
                pygame.draw.circle(screen, self.sensorial_field_color_danger, (int(self.x), int(self.y)), self.sensorial_radius, 3)
            elif self.in_follow:
                pygame.draw.circle(screen, self.sensorial_field_color_follow, (int(self.x), int(self.y)), self.sensorial_radius, 3)
            elif self.in_critical:
                pygame.draw.circle(screen, self.sensorial_field_color_critical, (int(self.x), int(self.y)), self.sensorial_radius, 3)
            else:
                pygame.draw.circle(screen, self.sensorial_field_color, (int(self.x), int(self.y)), self.sensorial_radius, 1)
    
    def get_pos(self) -> tuple:
        """Returns Survivor coordinates.

        Returns:
            tuple: Survivor coordinates.
        """        
        return self.x, self.y

class Danger:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.edge = 20
        self.color = [255, 0, 0]
        self.damage = 2
    
    def show(self):
        danger_rect = pygame.Rect(self.x, self.y, self.edge, self.edge)
        pygame.draw.rect(screen, tuple(self.color), danger_rect)

    def get_pos(self):
        return self.x + self.edge // 2, self.y + self.edge // 2

class Food:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.color = [0, 255, 0]
        self.edge = 20
        self.field_radius = self.edge * 2
        self.quantity = 20
        self.energy_bonus = 1
    
    def show(self):
        food_rect = pygame.Rect(self.x, self.y, self.edge, self.edge)
        pygame.draw.rect(screen, tuple(self.color), food_rect)
        pygame.draw.circle(screen, (0, 255, 0), (self.x + self.edge//2, self.y + self.edge//2), self.field_radius, 3)
    
    def get_pos(self):
        return self.x, self.y

danger = Danger(random.randint(50, WIDTH-50), random.randint(50, HEIGHT-50))
food = Food(WIDTH//2, HEIGHT//2)

survivor_zero = Survivor(0, 0) # Survivor model
survivors = []

# - - - - - - - - - - SURVIVORS CREATION - - - - - - - - - -
for _ in range(NB_OF_SURVIVORS):
    radius = survivor_zero.sensorial_radius
    limit_edge = survivor_zero.sensorial_radius

    # The Survivor's coordinates are generated in such a way that the 
    # Danger isn't in his sensory field and so that it's not too close 
    # to the edge of the surface.
    far_enough_from_danger = False
    while not far_enough_from_danger:
        x = random.randint(limit_edge, WIDTH - limit_edge)
        y = random.randint(limit_edge, HEIGHT - limit_edge)
        if get_distance((x, y), danger.get_pos()) <= radius + danger.edge:
            print("TOO CLOSE AVOIDED")
            continue
        else:
            far_enough_from_danger = True

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
    screen.fill(WHITE)

    # - - - - - - - - - - DANGER DETECTION - - - - - - - - - -
    for survivor in survivors:
        #print(survivor.energy, end="\r")

        # Recovering the distance between Survivor and Danger
        danger_distance = get_distance(survivor.get_pos(), danger.get_pos())
        
        # Danger is in the area of Survivor's sensory field.
        # Survivor enters 'in_danger' mode and an escape 
        # vector is generated.
        if danger_distance - (danger.edge/2) < survivor.sensorial_radius:
            survivor.in_danger = True

            # The difference between the Survivor and 
            # Danger coordinates is calculated. This 
            # gives the horizontal and vertical components
            # of the vector from Danger to Survivor.
            dx = survivor.x - danger.x
            dy = survivor.y - danger.y

            # Vector normalization by Pythagorean theorem.
            norm = np.sqrt(dx**2 + dy**2)
            if norm != 0:
                survivor.dx = dx / norm
                survivor.dy = dy / norm

    # - - - - - - - - - - FOLLOW DETECTION - - - - - - - - - -
    for survivor in survivors:
        # If a Survivor encounters another Survivor in 
        # danger within its sensory field, it follows it 
        # as it flees.
        survivor.in_follow = False
        if not survivor.in_danger:
            for other_survivor in survivors:
                if other_survivor != survivor and other_survivor.in_danger:
                    if get_distance(survivor.get_pos(), other_survivor.get_pos()) < survivor.sensorial_radius + other_survivor.sensorial_radius:
                        survivor.in_follow = True
                        survivor.dx = other_survivor.dx
                        survivor.dy = other_survivor.dy
                        break  # Another Survivor in danger

    # - - - - - - - - - - MOVE & SHOW SURVIVORS - - - - - - - - - -
    
    # Deleting an element from a list during its iteration can lead 
    # to unforeseen behavior, so the Survivor to be deleted is stored 
    # in this list to avoid deleting it during the iteration of the 
    # Survivor list.
    to_remove = []

    for idx, survivor in enumerate(survivors):
        if idx == 0:
            print(survivor.energy, end="\r")

        # If the method returns True, the Survivor must be deleted.
        should_remove = survivor.move()
        #survivor.show()
        if not should_remove:
            survivor.show()
        else:
            to_remove.append(survivor)

        if SHOW_DISTANCE_LINE:
            pygame.draw.line(screen, (255,0,0), survivor.get_pos(), danger.get_pos())

    # - - - - - - - - - - THE REAPER ROOM - - - - - - - - - -
    # Survivors deletion
    for survivor in to_remove:
        survivors.remove(survivor)

    # - - - - - - - - - - OTHER - - - - - - - - - -
    danger.show()
    food.show()

    pygame.display.flip() # Updating display
    clock.tick(FPS) # FPS Limit 

pygame.quit()