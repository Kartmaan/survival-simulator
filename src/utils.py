from src.pygame_options import pygame
from pygame.math import Vector2
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

def name_generator(syllables_min=2, syllables_max=4, suffix=False) -> str:
    """
    Generates a name for Survivors by combining syllables.

    Args:
        syllables_min (int): Minimum number of syllables.
        syllables_max (int): Maximum number of syllables.
        suffix (bool, optional): Suffixes is added occasionally. Defaults to False.

    Returns:
        str: The generated name.
    """

    # Basic syllables
    beginning_syllables = ["ba", "be", "bi", "bo", "bu", "da", "de", "di", "do", "du",
                     "fa", "fe", "fi", "fo", "fu", "ga", "ge", "gi", "go", "gu",
                     "ha", "he", "hi", "ho", "hu", "ja", "je", "ji", "jo", "ju",
                     "ka", "ke", "ki", "ko", "ku", "la", "le", "li", "lo", "lu",
                     "ma", "me", "mi", "mo", "mu", "na", "ne", "ni", "no", "nu",
                     "pa", "pe", "pi", "po", "pu", "ra", "re", "ri", "ro", "ru",
                     "sa", "se", "si", "so", "su", "ta", "te", "ti", "to", "tu",
                     "va", "ve", "vi", "vo", "vu", "wa", "we", "wi", "wo", "wu",
                     "ya", "ye", "yi", "yo", "yu", "za", "ze", "zi", "zo", "zu"]

    middle_syllables = ["la", "le", "li", "lo", "lu", "ra", "re", "ri", "ro", "ru",
                      "na", "ne", "ni", "no", "nu", "ma", "me", "mi", "mo", "mu",
                      "ga", "ge", "gi", "go", "gu", "da", "de", "di", "do", "du",
                      "ba", "be", "bi", "bo", "bu"]

    final_syllables = ["ar", "er", "ir", "or", "ur", "al", "el", "il", "ol", "ul",
                   "an", "en", "in", "on", "un", "as", "es", "is", "os", "us",
                   "ard", "erd", "ird", "ord", "urd", "ald", "eld", "ild", "old", "uld",
                   "and", "end", "ind", "ond", "und", "ast", "est", "ist", "ost", "ust"]

    suffixes = ["The Beast", "The Survivor", "The Last", ]

    # Choice of a random number of syllables
    nb_of_syllables = np.random.randint(syllables_min, syllables_max)

    name_parts = []
    final_name = []

    # Building the body of a name with syllables
    for i in range(nb_of_syllables):
        if i == 0:
            name_parts.append(np.random.choice(beginning_syllables)) # beginning syllable
        elif i == nb_of_syllables - 1:
            name_parts.append(np.random.choice(final_syllables))   # middle syllable
        else:
            name_parts.append(np.random.choice(middle_syllables)) # final syllable

    final_name.append("".join(name_parts).capitalize())

    # Add a suffix (optional)
    if suffix and np.random.random() < 0.2: # proba 20%
        final_name.append(np.random.choice(suffixes))

    # Assembling the parts
    name = " ".join(final_name)

    return name