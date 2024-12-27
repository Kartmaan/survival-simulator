import pygame
import random
import numpy as np

# Initialisation de Pygame
pygame.init()

# Dimensions de l'écran
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Simulation de Vivants")

# Couleurs
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)

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
  distance = np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
  return distance

def angle(survivor_pos: tuple, danger_pos: tuple):
    return np.arctan2(danger_pos[1] - survivor_pos[1], danger_pos[0], survivor_pos[0])

class Survivor:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.dx = 0.0
        self.dy = 0.0
        self.speed = 4

        self.survivor_radius = 5
        self.sensorial_radius = self.survivor_radius * 10

        self.color = [0, 200, 0]
        self.color_danger = [200, 0, 0]

        self.flee_speed = self.speed + 2
        self.flee_counter = 0
        self.flee_duration = 60

        self.direction_time = random.randint(30,50)
        self.direction_counter = 0

        self.in_danger = False
        self.energy = 50

    def change_direction(self):
        """Choosing a random direction by randomly changing 
        the values of dx and dy.

        In the 'move' method, the Survivor's x and y 
        values are added to dx and dy respectively, 
        which can be between -1 and 1, to establish the 
        direction of the next step. The variation in x 
        and y can therefore be positive or negative.
        """        
        self.dx = random.uniform(-1, 1)  # Direction aléatoire en x
        self.dy = random.uniform(-1, 1)  # Direction aléatoire en y

    def move(self):
        """Moves the Survivor in two different modes:
            - Search mode: the Survivor moves randomly 
            across the surface in search of food.
            - Escape mode: the Survivor perceives danger 
            in its sensory field, and flees by increasing 
            its speed.
        """
        if not self.in_danger:
            self.x += self.dx * self.speed
            self.y += self.dy * self.speed

        else:
            self.x += self.dx * self.flee_speed
            self.y += self.dy * self.flee_speed

            self.flee_counter += 1
            if self.flee_counter >= self.flee_duration:
                self.in_danger = False
                self.flee_counter = 0

        # If the Survivor goes out on one side of the 
        # surface, it comes back in on the other.
        #
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
        
        # 
        self.direction_counter +=1
        if self.direction_counter >= self.direction_time:
            self.change_direction()
            self.direction_time = random.randint(30, 60)
            self.direction_counter = 0

    def show(self):
        if not self.in_danger:
            pygame.draw.circle(screen, tuple(self.color), (int(self.x), int(self.y)), self.survivor_radius)
            pygame.draw.circle(screen, (0, 0, 0), (int(self.x), int(self.y)), self.sensorial_radius, 1)
        else:
            pygame.draw.circle(screen, tuple(self.color_danger), (int(self.x), int(self.y)), self.survivor_radius)
            pygame.draw.circle(screen, (255, 0, 0), (int(self.x), int(self.y)), self.sensorial_radius, 3)

    def get_pos(self):
        return self.x, self.y

class Danger:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.edge = 20
        self.color = [255, 0, 0]
    
    def show(self):
        danger_rect = pygame.Rect(self.x, self.y, self.edge, self.edge)
        pygame.draw.rect(screen, tuple(self.color), danger_rect)

    def get_pos(self):
        return self.x + self.edge // 2, self.y + self.edge // 2

danger = Danger(WIDTH//2, HEIGHT//2)

survivors = []

for _ in range(10):  # Création de vivants
    radius = 5

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
clock = pygame.time.Clock() #Pour gérer les FPS
FPS = 30
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Surface erasing
    screen.fill(WHITE)

    # Updating and displaying Survivors
    for survivor in survivors:
        # Recovering the distance between Survivor and 
        # Danger
        danger_distance = get_distance(survivor.get_pos(), danger.get_pos())
        
        # Danger is in the area of Survivor's sensory field.
        # Survivor enters 'in_danger' mode and an escape 
        # vector is generated.
        if danger_distance < survivor.sensorial_radius:
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
        
        elif not survivor.in_danger:
            survivor.flee_counter = 0

        survivor.move()
        survivor.show()

        #pygame.draw.line(screen, (255,0,0), survivor.get_pos(), danger.get_pos())
    
    danger.show()

    pygame.display.flip() # Updating display
    clock.tick(FPS) # FPS Limit 

pygame.quit()