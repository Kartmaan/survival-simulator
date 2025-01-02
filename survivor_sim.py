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

# Couleurs
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)

NB_OF_SURVIVORS = 1

def midpoint(point1: tuple, 
             point2: tuple,
             offset: float = 0.0) -> pygame.math.Vector2:
    """Returns the central point between two coordinates or a 
    point offset from this center

    Args:
        point1 : Coordinates of the 1st point
        point2 : Coordinates of the 2nd point
        offset : Offset from center (-/+) (default = 0.0)

    Returns:
        tuple: The coordinates of the desired point
    """
    x = (point1[0] + point2[0]) / 2 + offset * (point2[0] - point1[0]) / np.linalg.norm([point2[0] - point1[0], point2[1] - point1[1]])
    y = (point1[1] + point2[1]) / 2 + offset * (point2[1] - point1[1]) / np.linalg.norm([point2[0] - point1[0], point2[1] - point1[1]])
    
    return pygame.math.Vector2(x, y)

def get_distance(p1: tuple, p2: tuple) -> float:
  """Returns the Euclidean distance between two coordinates

  Args:
  p1 : First coordinates
  p2 : Second coordinates

  Returns:
  The distance between the two coordinates 
  """
  #distance = np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
  distance = np.linalg.norm(np.array(p2) - np.array(p1))
  return distance

def angle(survivor_pos: tuple, danger_pos: tuple):
    return np.arctan2(danger_pos[1] - survivor_pos[1], danger_pos[0], survivor_pos[0])

class Survivor:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.dx = 0.0
        self.dy = 0.0

        self.speed_default = 4
        self.speed = self.speed_default
        self.speed_critical = self.speed / 2

        self.timers = {}

        self.survivor_radius_default = 10
        self.survivor_radius = self.survivor_radius_default
        
        self.sensorial_radius_default = self.survivor_radius * 5
        self.sensorial_radius = self.survivor_radius_default

        self.color = [0, 200, 0]
        self.color_danger = [200, 0, 0]

        self.flee_speed = self.speed + 2
        self.flee_duration = 3

        self.in_danger = False
        self.in_follow = False

        self.energy_default = 50
        self.energy = self.energy_default
        self.in_critical = False
        self.energy_critical = self.energy_default / 4
        self.energy_loss_frequency = 1 # In second
        self.energy_loss_normal = 0.5 # Per second
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
        current_time = pygame.time.get_ticks() / 1000.0
        
        # If the timer name isn't present in the 
        # 'self.timers' dictionary keys, it's added, with 
        # the current time as value (it acts as a fixed 
        # time reference point for calculating durations).
        # The function returns False, as the timer has 
        # just been added and therefore cannot have 
        # already elapsed.
        if timer_name not in self.timers:
            self.timers[timer_name] = current_time
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
        elapsed_time = current_time - self.timers[timer_name]
        if elapsed_time >= duration:
            self.timers[timer_name] = current_time
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
    
    def move(self):
        """Moves the Survivor in two different modes:
            - Search mode: the Survivor moves randomly 
            across the surface in search of food.
            - Escape mode: the Survivor perceives danger 
            in its sensory field, and flees by increasing 
            its speed.
        """
        if self.energy <= self.energy_critical:
            self.in_critical = True
        else:
            self.in_critical = False

        if self.in_critical and self.sensorial_radius > self.survivor_radius:
            if self.timer("sensorial_radius", 0.5):
                new_radius = (self.energy / self.energy_critical) * self.sensorial_radius_default
                self.sensorial_radius = new_radius
        else:
            self.sensorial_radius = self.sensorial_radius_default
        
        # Search mode : not in danger
        if not self.in_danger:
            self.x += self.dx * self.speed
            self.y += self.dy * self.speed

            if self.timer("energy_loss", self.energy_loss_frequency):
                self.energy -= self.energy_loss_normal

            if self.timer("direction", random.uniform(2,7)):
                self.change_direction()

        # Escape mode : in danger
        else:
            self.x += self.dx * self.flee_speed
            self.y += self.dy * self.flee_speed

            if self.timer("energy_loss", self.energy_loss_frequency):
                self.energy -= self.energy_loss_danger

            if self.timer("flee", self.flee_duration):
                self.in_danger = False

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

        if self.energy <= 0:
            self.energy = 0

    def show(self):
        # Survivor is in danger
        if self.in_danger and not self.in_follow:
            pygame.draw.circle(screen, tuple(self.color_danger), (int(self.x), int(self.y)), self.survivor_radius)
            pygame.draw.circle(screen, (255, 0, 0), (int(self.x), int(self.y)), self.sensorial_radius, 3)

        # Survivor follows an other Survivor in danger
        elif self.in_follow: #and not self.in_danger:
            pygame.draw.circle(screen, tuple(self.color_danger), (int(self.x), int(self.y)), self.survivor_radius)
            pygame.draw.circle(screen, (255, 165, 0), (int(self.x), int(self.y)), self.sensorial_radius, 3)

        elif self.in_critical:
            pygame.draw.circle(screen, (42, 42, 42), (int(self.x), int(self.y)), self.survivor_radius)
            pygame.draw.circle(screen, (0, 0, 0), (int(self.x), int(self.y)), self.sensorial_radius, 1)

        # Survivor is ok
        else:
            pygame.draw.circle(screen, tuple(self.color), (int(self.x), int(self.y)), self.survivor_radius)
            pygame.draw.circle(screen, (0, 0, 0), (int(self.x), int(self.y)), self.sensorial_radius, 1)

    def get_pos(self):
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

for _ in range(NB_OF_SURVIVORS):
    radius = survivor_zero.survivor_radius

    far_enough_from_danger = False
    while not far_enough_from_danger:
        x = random.randint(10, WIDTH - 10)
        y = random.randint(10, HEIGHT - 10)
        if get_distance((x, y), danger.get_pos()) <= radius + danger.edge:
            print("TOO CLOSE AVOIDED")
            continue
        else:
            far_enough_from_danger = True

    survivor = Survivor(x, y)
    survivors.append(survivor)

# Boucle principale
running = True
clock = pygame.time.Clock()
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Surface erasing
    screen.fill(WHITE)

    # Updating and displaying Survivors
    for survivor in survivors:
        #print(survivor.energy, end="\r")
        # - - - - Direct contact with danger - - - -
        # Recovering the distance between Survivor and 
        # Danger
        danger_distance = get_distance(survivor.get_pos(), danger.get_pos())
        
        # Danger is in the area of Survivor's sensory field.
        # Survivor enters 'in_danger' mode and an escape 
        # vector is generated.
        if danger_distance - 5 < survivor.sensorial_radius:
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

    # - - - - Interaction with other survivors - - - -
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

    # Move and show survivors
    for survivor in survivors:
        print(survivor.energy, end="\r")
        
        survivor.move()
        survivor.show()

        #pygame.draw.line(screen, (255,0,0), survivor.get_pos(), danger.get_pos())
    
    danger.show()
    food.show()

    pygame.display.flip() # Updating display
    clock.tick(FPS) # FPS Limit 

pygame.quit()