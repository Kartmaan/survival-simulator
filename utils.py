from pygame_options import pygame
from pygame.math import Vector2
import random # Imported from other modules
import numpy as np # Imported from other modules

def get_distance(p1: Vector2, p2: Vector2) -> float:
  """Returns the Euclidean distance between two coordinates.

  Args:
  p1 : First coordinates
  p2 : Second coordinates

  Returns:
  The distance between the two coordinates
  """
  #distance = np.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)
  #distance = np.linalg.norm(np.array(p2) - np.array(p1))
  distance = p1.distance_to(p2)
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