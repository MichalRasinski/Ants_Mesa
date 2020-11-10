# Ants_Mesa

So far:

Ants:
- die if health is zero
- some percent stays at the colony
- when foraging go more or less in one direction
- if are next to an enemy ant, then they attack
- if are next to a food site, then they pick food and go to the home colony based on their smell
- if they carry food and are next to the home colony then they leave it there

Colonies:
- spawn ants: the probability of an ant getting born is expressed by the formula: 

    birth_prob = 0.05 * min(10, food_units // birth_food) + 0.2 + 0.075 * (reproduction_rate - 1),
    where, birth_food is ant_size * FOOD_SIZE_BIRTH_RATIO                 
- shelter ants
- stores food

FoodSites:
- store food
- regenerate food if they are renewable

