# Survival simulator

Simulation of survivors on the move in search of food, avoiding dangers and trying, as best they can, to resist harsh climates thanks to their specific characteristics.


https://github.com/user-attachments/assets/689de7b2-a5a9-402a-a27c-f3f276ebda94


## Entities
The simulation is based on 3 entities that influence each other, directly or indirectly :

### Survivor
Entities generated and moving in search of food. They have several survival mechanisms :

#### Sensorial radius
- The Survivor has a sensorial field that allows it to detect food, danger and other Survivors.
- All Survivors are generated with the same sensorial field size
- The radius of this field can be reduced if the Survivor is in a critical condition.

#### Energy management:
- When a Survivor is created, it has a specific amount of energy.
- This energy value decreases as it moves.
- This loss of energy varies according to the Survivor's state: it is minimal if it's just looking for food, and 
maximum if it's fleeing danger.
- If the Survivor reaches a critical energy threshold, its speed is reduced, as is the size of its sensorial radius.
- If its energy drops to zero, it comes to a standstill before disappearing shortly afterward.
- The Survivor can recover energy by finding food.

#### Danger management
- When the Survivor detects danger in his sensorial field, he flees by increasing his speed and expending more energy.
- During his escape, the Survivor ignores food

**Spatial memory**
- When encountering danger, the Survivor establishes a **safety distance** from it, and keeps it for a certain period 
of time, defined by its **spatial memory**, so as not to cross it. 
- During this period, the Survivor enters 'deja_vu' mode, meaning he has recently come into contact with the danger 
and still remembers his position.
- If this safety distance is reached during the 'deja_vu' mode, the Survivor turns back before the danger reaches 
its sensory field.
- The duration of this **spatial memory** is proportional to the Survivor's energy level at the time of contact with the 
danger. The higher **the energy level, the longer the memory**.

![Danger management](/assets/md_images/danger.png)

**Audacity**
- Survivor has a random “**audacity**” value (between 1.0 and 10.0) that determines the length of this safety distance 
from the danger but also the duration of its flee. 
- The lower the audacity value, the greater the safe distance, which, while guaranteeing the Survivor a better chance 
to not meet the danger, also deprives him of a greater range of movement, potentially preventing him from accessing a 
food zone.
- Conversely, a higher audacity value will reduce this safe distance, allowing the Survivor to access a wider area of 
the surface while ensuring he remains relatively far from danger.
- A high audacity value reduces the duration of the escape, allowing the Survivor to resume his search for food more 
quickly.
- Conversely, a low audacity value increases the duration of the escape, which certainly ensures greater distance from 
danger, but also causes the Survivor to consume more energy during its prolonged escape, during which time its search 
for food is ignored.

![Audacity management](/assets/md_images/audacity.png)

> While Survivors start out on an equal footing in terms of their main parameters: same initial energy value, same 
sensory radius size, same speed, same energy loss value, etc., the audacity value makes it possible to include 
randomness in their behavior without significantly impacting the imbalance in survival chances. 

**Follow**
- If a Survivor detects another fleeing Survivor in his sensory field, he follows him out of a sense of survival.
- If a Survivor in '**deja_vu**' mode detects another Survivor fleeing, it doesn't follow, as it already knows where 
the danger is.

![Follow management](/assets/md_images/follow.png)

#### Food management
- When the Survivor's energy level drops sufficiently, he starts to feel hungry.
- When the scent of food is detected by the Survivor's sensory field, the Survivor only begins to rush under certain 
conditions :
  - The Survivor's energy value must be less than or equal to a **hunger** threshold.
  - The Survivor must be **able to eat**: for example, after eating, the Survivor must not eat again for a period of 
  time determined by a cooldown.
  - A vacant place must be available for eating, as the food can only be consumed by a limited number of Survivors.
  - Survivor must not be in danger or in pursuit of a Survivor in danger.
  - The Survivor must have an energy value greater than zero. If the Survivor becomes immobilized for lack of energy 
  while in direct proximity to the food, it will not be saved.
- It consumes food until its energy level reaches a maximum, or until there is no more food to consume.
- Its consumption speed will be higher if its energy level is critical.

Beyond these survival mechanics, the Survivor also has a unique, randomly-generated name that allows it to be precisely 
identified. This name is used to distinguish one Survivor from another during the podium phase (_see below_).

#### Resilience
- The Survivor has a random resilience value (between 1.0 and 10.0).
- Resilience is a parameter that influences how a Survivor copes with the negative effects of its environment and 
especially the climate (see Weather section).
- The value acts as a mitigating factor for penalties applied to certain dynamic values, such as speed, energy loss, or 
other statistics influenced by external conditions.
  - The higher the resilience, the lower the penalties applied to a statistic.
  - The lower the resilience, the greater the penalties incurred by the entity.
- The value allows to : 
  - Reduce the negative impact of extreme environmental conditions (_too low or too high temperatures_) on the 
  Survivor's speed
  - Reduce the effect of malus related to Survivor energy loss.
- Each climate has a basic and fixed penalty multiplier to be applied to certain dynamic values of the Survivor, 
such as its speed or energy loss value. It's the effect of this multiplier that is attenuated by the Survivor's 
resilience attribute.

> Resilience introduces additional variability on the simulation (_in addition to the 'audacity' attribute_) 
depending on the characteristics of each entity and the climate.

### Food
Food consumed by Survivors to boost their energy levels.

- Food has an **olfactory field** that can be detected by the Survivor's sensory field.
- It has a random **quantity value** that decreases as it is consumed by Survivors.
- The olfactory field shrinks as food is consumed.
- When its energy value reaches zero, **Food disappears to appear somewhere else** after a given time.
- Each time it appears, a new quantity value is randomly defined.
- A **limited number of Survivors** can consume the Food simultaneously.

![Food management](/assets/md_images/food.png)

### Danger
Entity attacking Survivor for unknown reason.

- The Danger is posted at a random location on the surface.
- It has a **rage level** that determines the amount of damage it inflicts.
- It **attacks Survivors** who get too close to it.
- When attacking, the Danger moves rapidly back and forth in the direction of the targeted Survivor.
- Each attack **increases its rage level** to a maximum threshold, which increases the damage inflicted.
- To illustrate its rage level, the Danger has a **rotation speed** proportional to its rage score.
- When the Danger spends a certain amount of time without attacking, its **rage level decreases**.

## Weather
The simulation alternates between several climates, each with a different impact on the entities in the simulation.

- The climate loop is as follows: [temperate 🍃, cold ❄, temperate 🍃, hot 🔥]

![Weather](/assets/md_images/weather.png)


- Cold ❄ and hot 🔥 climates essentially imply malus 🔴 for Survivors, but at least give them an advantage 🟢.
- A temperature is updated periodically, centered around a climatic temperature mean and respecting a given standard 
deviation.
- These temperatures have a direct impact on Survivors, with greater or lesser malus depending on the deviation from a 
universal reference temperature.
- The simulation defines the basic malus applied to certain dynamic variables for each climate, for example :
  - cold_seed_penalty = 0.4
  - hot_speed_penalty = 0.6
  - temperate_speed_penalty = 1 
- These penalty multipliers are weighted by temperature.
- All temperate climate penalty multipliers are set to 1, which means that all parameters will be nominal.
- On the other hand, since the temperate mean is also the universal reference temperature, any deviation towards the 
positive (hot) or negative (cold) will incur a slight penalty.
- These temperature deviations around climate averages are controlled by standard deviations, to prevent a temperature 
from reaching a climate value that is not its own.

![Temperature](/assets/md_images/temperature.png)

- **❄. Impact of cold climate :**
  - **Survivors**
    - Move slower 🔴
    - Lose more energy 🔴
  - **Food**
    - Respawn later 🔴
    - Less quantity 🔴
    - Slower decay 🟢


- **🔥. Impact of hot climate :**
  - **Survivors**
    - Move slower 🔴
    - Lose more energy 🔴
  - **Food**
    - Less quantity 🔴
    - Faster decay 🔴
    - Respawn later 🔴
  - **Danger**
    - Loses rage faster 🟢


- **🍃. Impact of temperate climate :**
  - All simulation parameters are nominal


- The malus applied to Survivors are weighted by their resilience and energy values but also the climatic temperature.

![Weighting](/assets/md_images/weighting.png)

- Each time the climate changes, the background color changes by fading.

## Podium
- When the Survivor population becomes sufficiently low, the three Survivors with the highest energy values are 
highlighted. 
- Their names appear next to them and are marked with a cross.
- The thickest cross indicates first place on the podium.
- When there's only one Survivor left, the simulation stops and a floating window appears, highlighting the winner and 
- displaying a few statistics about it.

## Debug
- A debug mode is also available to display precise information on the state of the simulation on screen, in real time.
![Debug on screen](/assets/md_images/debug.png)
- At the end of each simulation, a `.log` file is also created to analyze the course of the simulation in greater detail 
and highlight any problems. 
![Logger](/assets/md_images/logger.png)
