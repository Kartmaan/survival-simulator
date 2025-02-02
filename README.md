# Survivor simulator

A Pygame simulation in which survivors search for food while facing danger. 

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
- The Survivor's energy recovery speed will be faster if it's in a critical state.

#### Danger management, spatial memory and audacity
- When the Survivor detects danger in his sensorial field, he flees by increasing his speed and expending more energy.
- During his escape, the Survivor ignores food
- When encountering danger, the Survivor establishes a **safety distance** from it, and keeps it for a certain period 
of time, defined by its **spatial memory**, so as not to cross it.
- During this period, the Survivor enters 'deja_vu' mode, meaning he has recently come into contact with the danger 
and still remembers his position.
- If this safety distance is reached during the 'deja_vu' mode, the Survivor turns back before the danger reaches 
its sensory field.
- The duration of this **spatial memory** is proportional to the Survivor's energy level at the time of contact with the 
danger. The higher **the energy level, the longer the memory**.

![Danger management](/assets/md_images/danger.png)

- Survivor has a random float “**audacity**” value between 1.0 and 10.0 that determines the length of this safety 
distance from the danger. 
- The lower the audacity value, the greater the safe distance, which, while guaranteeing the Survivor a better chance 
to not meet the danger, also deprives him of a greater range of movement, potentially preventing him from accessing a 
food zone.
- Conversely, a higher audacity value will reduce this safe distance, allowing the Survivor to access a wider area of 
the surface while ensuring he remains relatively far from danger.

![Audacity management](/assets/md_images/audacity.png)

- If a Survivor detects another fleeing Survivor in his sensory field, he follows him out of a sense of survival.
- If a Survivor in '**deja_vu**' mode detects another Survivor fleeing, it doesn't follow, as it already knows where 
the danger is.

![Follow detection](/assets/md_images/follow.png)

#### Food management
- When the Survivor's energy level drops sufficiently, he starts to feel hungry.
- When food enters the Survivor's sensory field, when he's hungry and when this food can accommodate a new eater, 
he heads towards it to consume it.
- It consumes food until its energy level reaches a maximum, or until there is no more food to consume.
- Its consumption speed will be higher if its energy level is critical.

Beyond these survival mechanics, the Survivor also has a unique, randomly-generated name that allows it to be precisely 
identified. This name is used to distinguish one Survivor from another during the podium phase (_see below_).

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

## Podium
- When the Survivor population becomes sufficiently low, the three Survivors with the highest energy values are 
highlighted. 
- Their names appear next to them and are marked with a cross.
- The thickest cross indicates first place on the podium