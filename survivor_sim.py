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
BLANC = (255, 255, 255)
NOIR = (0, 0, 0)
ROUGE = (255, 0, 0)

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

def triangle(center_pos: tuple, base_length: int, height: int):
    center_base = (center_pos[0], center_pos[1] + height // 2)
    p1 = (center_base[0] - base_length // 2, center_base[1])
    p2 = (p1[0] + base_length, p1[1])
    p3 = (center_pos[0], center_pos[1] - height // 2)

    pygame.draw.polygon(screen, (255, 0, 0), [p1, p2, p3])

class Survivor:
    def __init__(self, x, y, radius, speed):
        self.x = x
        self.y = y
        self.dx = 0.0
        self.dy = 0.0
        self.radius = radius
        self.sensorial_radius = self.radius * 10
        self.color = [0, 0, 0]
        self.color_danger = [200, 0, 0]
        self.speed = speed
        self.direction_time = random.randint(30,90)
        self.direction_counter = 0
        self.in_danger = False

    def change_direction(self):
        self.dx = random.uniform(-1, 1)  # Direction aléatoire en x
        self.dy = random.uniform(-1, 1)  # Direction aléatoire en y

    def move(self):
        self.x += self.dx * self.speed
        self.y += self.dy * self.speed

        # Infinite space
        if self.x + self.radius < 0:
            self.x = WIDTH + self.radius
        elif self.x - self.radius > WIDTH:
            self.x = -self.radius
        
        if self.y + self.radius < 0:
            self.y = HEIGHT + self.radius
        elif self.y - self.radius > HEIGHT:
            self.y = -self.radius
        
        self.direction_counter +=1
        if self.direction_counter >= self.direction_time:
            self.change_direction()
            self.direction_time = random.randint(30, 90)
            self.direction_counter = 0

    def show(self):
        if not self.in_danger:
            pygame.draw.circle(screen, tuple(self.color), (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, (0, 0, 0), (int(self.x), int(self.y)), self.sensorial_radius, 1)
        else:
            pygame.draw.circle(screen, tuple(self.color_danger), (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, (255, 0, 0), (int(self.x), int(self.y)), self.sensorial_radius, 3)


    def get_pos(self):
        return self.x, self.y
    
class Food:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.edge = 10
        self.color = [0, 0, 255]
    
    def show(self):
        food_rect = pygame.Rect(self.x, self.y, self.edge, self.edge)
        pygame.draw.rect(screen, tuple(self.color), food_rect)

    def get_pos(self):
        return self.x + self.edge // 2, self.y + self.edge // 2

class Danger:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.edge = 20
        #self.base_length = 20
        #self.height = 20
        self.color = [255, 0, 0]
    
    def show(self):
        #triangle(center_pos=(x, y), base_length= self.base_length, height= self.height)
        danger_rect = pygame.Rect(self.x, self.y, self.edge, self.edge)
        pygame.draw.rect(screen, tuple(self.color), danger_rect)

    def get_pos(self):
        return self.x + self.edge // 2, self.y + self.edge // 2

# Création des vivants
survivors = []
#vivants = list([Vivant])

for _ in range(5):  # Création de 20 vivants
    x = random.randint(50, WIDTH - 50)
    y = random.randint(50, HEIGHT - 50)
    rayon = random.randint(5, 15)
    vitesse = random.uniform(3, 5)
    survivor = Survivor(x, y, rayon, vitesse)
    survivors.append(survivor)

""" foods = []
for _ in range(1):
    x = random.randint(50, WIDTH - 50)
    y = random.randint(50, HEIGHT - 50)
    food = Food(x, y)
    foods.append(food) """

x = random.randint(50, WIDTH - 50)
y = random.randint(50, HEIGHT - 50)
food = Food(x, y)

""" dangers = []
for _ in range(1):
    danger = Danger(100, 100)
    dangers.append(danger) """

danger = Danger(WIDTH//2, HEIGHT//2)

# Boucle principale
running = True
clock = pygame.time.Clock() #Pour gérer les FPS
FPS = 30
frames = 1
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Effacement de l'écran
    screen.fill(BLANC)


    # Mise à jour et affichage des vivants
    for survivor in survivors:
        frames += 1
        survivor.move()
        survivor.show()

        pygame.draw.line(screen, (255,0,0), survivor.get_pos(), danger.get_pos())
        #pygame.draw.line(screen, (0,0,255), vivant.get_pos(), food.get_pos())

        """ if frames % 50 == 0:
            print(get_distance(vivant.get_pos(), danger.get_pos()))
            print("VIVANT POS : ", vivant.get_pos())
            print("DANGER POS : ", danger.get_pos())
            print("SENSORIAL RADIUS : ", vivant.sensorial_radius)
            frames = 1 """

        if get_distance(survivor.get_pos(), danger.get_pos()) < survivor.sensorial_radius:
            survivor.in_danger = True
            #print("DANGER")
        else:
            survivor.in_danger = False

    """ for food in foods:
        food.show() """

    food.show()
    
    danger.show()

    # Mise à jour de l'affichage
    pygame.display.flip()
    clock.tick(FPS) #Limite les FPS

pygame.quit()