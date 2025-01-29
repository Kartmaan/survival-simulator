import pygame
from pygame.math import Vector2

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

def format_time(milliseconds: int) -> str:
    """
    Transforms a milliseconds value in the format hh:mm:ss:ms.

    Args:
        milliseconds (int): Value in milliseconds.

    Returns:
        str: Time in hh:mm:ss:ms format
    """
    ms = milliseconds % 1000
    seconds = (milliseconds // 1000) % 60
    minutes = (milliseconds // (1000 * 60)) % 60
    hours = milliseconds // (1000 * 60 * 60)

    formated_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}:{ms:03d}"
    return formated_time

def percent(partial_value, total_value) -> int:
    """
    Returns the percentage represented by a partial value over a total value.

    Args:
        partial_value: The partial value whose percentage we wish to estimate.
        total_value: The total value represents the 100%.

    Returns:
        int: Percentage in integer values
    """
    res = (partial_value/total_value) * 100
    return round(res, 2)