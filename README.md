# Ants_Mesa

So far:

Ants:
- die if health or energy is zero
- normally they stay at the colony unless there is 'food trail' pheromone nearby. Then they follow that pheromone trail.
- if they loose the trail, they try to go back to the anthill based on 'self' pheromone
- once in a while a foraging party goes out looking for food. Each ant goes more or less straight not following any trail.
- if are next to an enemy ant, then they attack
- if are next to a food site, then they pick food and go to the home colony based on the 'self' pheromone.
- if they carry food they leave 'food trail' pheromone, which strength is based on the abundance of the food site.
- if they carry food and are next to the home colony then they leave it there

Queens:
- goes more or less in one direction
- if they find an abundant food site then they start a new colony on that  

Anthills:
- spawn ants: the probability of an ant getting born is expressed by the formula: 
  
    birth_prob = 0.05 * min(10, food_units // birth_food) + 0.2 + 0.075 * (reproduction_rate - 1),
    
    where, birth_food is ant_size * FOOD_SIZE_BIRTH_RATIO
- spawns queens once in a while                 
- gives shelter to ants
- stores food
- releases ants if they smell 'food trail'
- releases foraging ants periodically

FoodSites:
- store food
- regenerate food if they are renewable

