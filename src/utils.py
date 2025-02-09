from typing import Optional

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

def penalty_weighting(
    base_multiplier: float,
    energy: Optional[float] = None,
    energy_max: Optional[float] = None,
    mean_climatic_temperature: Optional[float] = None,
    temperature: Optional[float] = None,
    resilience: Optional[float] = None,
    resilience_min_max: Optional[list[float]] = None,
    inverse_effect: bool = False,
) -> float:
    """
    Adjusts a given multiplier based on external conditions such as energy level, temperature, and resilience.

    This function applies weighting to a base multiplier, allowing it to be influenced by multiple factors:
    - Energy: Higher energy reduces penalties, while lower energy increases them.
    - Temperature: Deviations from a reference temperature introduce penalties.
    - Resilience: Acts as a resistance factor to counteract penalties.

    If `inverse_effect` is set to True, the effects are reversed (i.e., instead of reducing penalties, they increase).
    Weights a multiplier with energy and/or temperature values.

    Args:
        base_multiplier (float): The initial multiplier to be weighted.
        energy (Optional[float]): The current energy level of the entity (if applicable).
        energy_max (Optional[float]): The maximum energy level of the entity (if applicable).
        mean_climatic_temperature (Optional[float]): Mean climatic temperature from which to measure deviation.
        temperature (Optional[float]): The current temperature affecting the entity.
        resilience (Optional[float]): A value representing the entity's ability to resist penalties
        (default range: [1.0, 10.0]).
        resilience_min_max (Optional[list[float, float]]): A list containing the minimum and maximum values for
        resilience.
        inverse_effect (bool): If True, reverses the effect of each factor (e.g., penalties increase rather than
        decrease).

    Returns:
        float: The final weighted multiplier, ensuring it never drops below a minimum threshold.
    """

    # Energy-based adjustment
    if energy is not None and energy_max is not None:

        # Even if the Survivor has a maximum energy value, it still suffers a minimum penalty.
        min_effect = 0.85

        # # Calculation of an energy factor that reduces the penalty as energy increases.
        energy_factor = min_effect + (1 - min_effect) * (energy / energy_max)

        # Reverse effect (if activated): high energy increases the penalty rather than reducing it.
        if inverse_effect:
            energy_factor = 2 - energy_factor  # Inversion de l'effet.

        # Applying the energy effect to the base multiplier.
        base_multiplier *= energy_factor

    # Temperature-based adjustment
    if all(x is not None for x in (mean_climatic_temperature, temperature)):

        # Neutral reference temperature
        neutral_temperature = 15.0

        # Absolute difference between current temperature and defined mean climatic temperature.
        temp_diff = abs(temperature - mean_climatic_temperature)

        # Determines where the current temperature is in relation to its climatic mean temperature and the neutral
        # temperature. This allows to adjust the impact according to the deviation from the neutral temperature.
        closer_to_neutral_temp = abs(temperature - neutral_temperature) < abs(mean_climatic_temperature -
                                                                              neutral_temperature)

        step = 0.01 # Each degree of deviation reduces the multiplier by 1%.
        max_impact = 0.5 # Prevents the multiplier from being reduced by more than 50%

        # Calculating the temperature factor: the further away from 'neutral_temperature', the greater the impact.
        temp_factor = 1 - min(temp_diff * step, max_impact) # Max impact ±50%

        # If the current temperature is closer to the climate average than to the neutral temperature, the impact of
        # temperature is attenuated.
        if closer_to_neutral_temp:
            temp_factor = 1 + min(temp_diff * step, max_impact * 0.5)

        # In the case of an inverse effect, temperature has an amplified effect.
        if inverse_effect:
            temp_factor = 1 + min(temp_diff * step, max_impact) # Inversion: penalty increases

        # Apply temperature effect to base multiplier
        base_multiplier *= temp_factor

    # Constitution-based adjustment
    if resilience is not None and resilience_min_max is not None:
        resilience_min = resilience_min_max[0]
        resilience_max = resilience_min_max[1]

        # Resilience clamp
        # Ensure that resilience is within the defined range
        resilience = max(resilience_min, min(resilience_max, resilience))

        # Calculation of resilience factor :
        # The higher the resilience, the more it mitigates penalties.
        if inverse_effect:
            constitution_factor = 1 - ((resilience - resilience_min) / (resilience_max - resilience_min) * 0.1)
        else:
            constitution_factor = 1 + ((resilience - resilience_min) / (resilience_max - resilience_min) * 0.1)

        # Apply the resilience effect to the base multiplier
        base_multiplier *= constitution_factor

    # Returns the final value, ensuring that it does not fall below 0.1.
    return max(0.1, base_multiplier)