from mesa import Agent, Model
from mesa.space import *
from mesa.time import RandomActivation
import math

ANT_SIZE_CARGO_RATIO = 5  # cargo = X * ant_size
SIZE_HEALTH_RATIO = 2  # ant_health = X * ant_size
SIZE_DAMAGE_RATIO = 1  # inflicted_damage = X * ant_size
FOOD_SIZE_BIRTH_RATIO = 2  # X * ant_size = food to produce a new ant


def sign(x):
    if x == 0:
        return 0
    else:
        return int(x / abs(x))


class Species:
    def __init__(self, ant_size, base_reproduction_rate, id):
        self.id = id
        self.base_reproduction_rate = base_reproduction_rate
        self.ant_size = ant_size


class FoodSite(Agent):
    def __init__(self, unique_id, model, initial_food_units, regeneration_rate=0):
        super().__init__(unique_id, model)
        self.initial_food_units = initial_food_units
        self.food_units = initial_food_units
        self.rate = regeneration_rate

    def step(self):
        self.food_units = min(self.food_units + self.rate, self.initial_food_units)
        self.food_units += self.rate
        if self.food_units == 0:
            self.model.schedule.remove(self)
            self.model.grid.remove_agent(self)


# TODO feromone path
# TODO energy
class Ant(Agent):
    def __init__(self, unique_id, model, species, coordinates, home_colony, stays_inside):
        super().__init__(unique_id, model)
        self.stays_inside = stays_inside
        self.home_colony = home_colony
        self.size = species.ant_size
        self.health = self.size * SIZE_HEALTH_RATIO
        self.coordinates = coordinates
        self.species = species
        self.cargo = 0

    # just move to other cell
    def move(self, new_position):
        self.model.grid.move_agent(self, new_position)
        self.coordinates = new_position

    # get dictionary of objects in the 8-neighbourhood
    def check_neighbourhood(self):
        objects = {"enemies": [], "food": []}
        possible_steps = self.model.grid.get_neighborhood(self.coordinates, moore=True)
        for x, y in possible_steps:
            if any(self.model.grid[x][y]):
                for agent in self.model.grid[x][y]:
                    if isinstance(agent, FoodSite):
                        objects["food"].append(agent)
                    elif isinstance(agent, Ant) and agent.species.id != self.species.id:
                        objects["enemies"].append(agent)
        return objects

    # attack other ant
    def attack(self, agent):
        agent.health -= self.size * SIZE_DAMAGE_RATIO

    # home going
    def go_home(self):
        dx, dy = [a - b for a, b in zip(self.home_colony.coordinates, self.coordinates)]
        move_x = sign(dx)  # self.random.choice([0, sign(dx)])
        move_y = sign(dy)  # self.random.choice([0, sign(dy)])
        new_position = (self.coordinates[0] + move_x, self.coordinates[1] + move_y)
        self.move(new_position)

    # take food from the food_site
    def take_food(self, food_site: FoodSite) -> None:
        self.cargo = min(self.size * ANT_SIZE_CARGO_RATIO, food_site.food_units)
        food_site.food_units -= self.cargo

    # leave food at the colony
    def leave_food(self, colony):
        colony.food_units += self.cargo
        self.cargo = 0

    # just die
    def die(self):
        self.model.schedule.remove(self)
        self.model.grid.remove_agent(self)

    def step(self):
        if self.health <= 0:
            self.die()
        elif self.stays_inside:
            objects = self.check_neighbourhood()
            if objects["enemies"]:
                self.attack(objects["enemies"][0])
        elif self.cargo:
            if self.coordinates == self.home_colony.coordinates:
                self.leave_food(self.home_colony)
            else:
                self.go_home()
        else:
            objects = self.check_neighbourhood()
            if objects["enemies"]:
                self.attack(objects["enemies"][0])
            elif objects["food"]:
                self.take_food(objects["food"][0])
            else:
                possible_moves = self.model.grid.get_neighborhood(self.coordinates, moore=True)
                self.move(self.random.choice(possible_moves))


# class WorkerAnt(Ant):
#     def __init__(self, unique_id, model, species, size, coordinates, home_coord):
#         super().__init__(self, unique_id, model, species, size, coordinates, home_coord)
# class HomeAnt(Ant):
#     def __init__(self, unique_id, model, species, size, coordinates, home_coord):
#         super().__init__(self, unique_id, model, species, size, coordinates, home_coord)


class Queen(Ant):
    def __init__(self, unique_id, model, species, size):
        super().__init__(unique_id, model, species, size)


class Colony(Agent):
    def __init__(self, unique_id, model, species: Species, coordinates):
        super().__init__(unique_id, model)
        self.species = species
        self.food_units = 50
        self.coordinates = coordinates
        self.ants_inside = 0
        self.turn_counter = 0

    def step(self):
        self.food_units -= self.ants_inside * self.species.ant_size
        self.turn_counter += 1
        ants_to_spawn = self.turn_counter // self.species.base_reproduction_rate
        if ants_to_spawn and self.food_units > FOOD_SIZE_BIRTH_RATIO * self.species.ant_size:
            self.food_units -= self.species.ant_size * FOOD_SIZE_BIRTH_RATIO
            self.turn_counter -= self.species.base_reproduction_rate
            stays_inside = self.random.random() > 0.3
            ant = Ant(self.model.next_id(), self.model, self.species, self.coordinates, self, stays_inside)
            self.model.schedule.add(ant)
            self.model.grid.place_agent(ant, self.coordinates)

# TODO display number of ants
class AntsWorld(Model):
    def __init__(self, N_species, width, height):
        super().__init__()
        self.num_species = N_species
        self.grid = MultiGrid(width, height, False)
        self.schedule = RandomActivation(self)
        self.counter = 0
        # Create agents
        for i in range(self.num_species):
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            c = Colony(self.next_id(), self, Species(i + 1, i + 1, i), (x, y))
            self.schedule.add(c)
            self.grid.place_agent(c, (x, y))
        for _ in range(2 * self.num_species):
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            fs = FoodSite(self.next_id(), self, self.random.randrange(50), regeneration_rate=0 * self.random.random())
            self.schedule.add(fs)
            self.grid.place_agent(fs, (x, y))

    def step(self):
        self.schedule.step()
