import ant_agent
from mesa import Agent, Model
from mesa.space import *
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
from collections import defaultdict
import random

ANT_SIZE_CARGO_RATIO = 5  # cargo = X * ant_size
SIZE_HEALTH_RATIO = 2  # ant_health = X * ant_size
SIZE_DAMAGE_RATIO = 1  # inflicted_damage = X * ant_size
FOOD_SIZE_BIRTH_RATIO = 2  # X * ant_size = food to produce a new ant


# killed ant produces pheromone calling for help
# killed ant is a source of food
# starving ant may ask for food another ant

def sign(x):
    if x == 0:
        return 0
    return x // abs(x)


def count_ants(model, species_id):
    ants = filter(lambda x: isinstance(x, ant_agent.Ant) and x.species.id == species_id, model.schedule.agents)
    return len(list(ants))


class Species:
    def __init__(self, ant_size, reproduction_rate, id):
        self.id = id
        self.reproduction_rate = reproduction_rate
        self.ant_size = ant_size
        self.food_energy = 100 / self.ant_size


class Obstacle(Agent):
    def __init__(self, unique_id, model):
        super().__init__(unique_id, model)


class FoodSite(Agent):
    def __init__(self, unique_id, model, initial_food_units, coordinates, regeneration_rate=0):
        super().__init__(unique_id, model)
        self.initial_food_units = initial_food_units
        self.food_units = initial_food_units
        self.rate = regeneration_rate
        self.pos = coordinates

    def step(self):
        self.food_units = min(self.food_units + self.rate, self.initial_food_units)
        self.food_units += self.rate
        for x, y in self.model.pheromone_map.iter_neighborhood(self.pos, moore=True):
            self.model.pheromone_map[x][y]["food"] = 2
        if not self.food_units:
            self.model.schedule.remove(self)
            self.model.grid.remove_agent(self)


class Anthill(Agent):
    def __init__(self, unique_id, model, species, pos, food_units=50):
        super().__init__(unique_id, model)
        self.species = species
        self.food_units = food_units
        self.pos = pos
        self.ants_inside = []
        self.queens_inside = []
        self.surrounding_cells = self.model.grid.get_neighborhood(self.pos, moore=True)
        self.birth_food = self.species.ant_size * FOOD_SIZE_BIRTH_RATIO

    def release_ant(self):
        if self.queens_inside:
            ant = self.queens_inside.pop()
        else:
            ant = self.ants_inside.pop(0)
        pheromone_cells = ant.smell_cells_for("food trail", self.surrounding_cells)
        possible_locations = list(set(self.surrounding_cells) & self.model.grid.empties)
        weights = [1 for pl in possible_locations]
        if self.model.schedule.steps % 30 < 2:
            ant.forage = True

        if set(pheromone_cells) & self.model.grid.empties:
            possible_locations = list(set(pheromone_cells) & self.model.grid.empties)
            weights = [pheromone_cells[pl] for pl in possible_locations]
        ant.pos = random.choices(possible_locations, weights)[0]
        ant.orient = (ant.pos[0] - self.pos[0], ant.pos[1] - self.pos[1])
        self.model.grid.place_agent(ant, ant.pos)

    def make_ant(self, w_or_q):
        if w_or_q == "worker":
            self.food_units -= self.birth_food
            ant = ant_agent.Ant(self.model.next_id(), self.model, self.species, self.pos, self)
            self.ants_inside.append(ant)
        if w_or_q == "queen":
            self.food_units -= self.birth_food * 2
            ant = ant_agent.Queen(self.model.next_id(), self.model, self.species, self.pos, self)
            self.queens_inside.append(ant)
        self.model.schedule.add(ant)

    def step(self):
        if self.food_units > self.birth_food * 2:
            birth_prob = 0.05 * min(10, self.food_units // self.birth_food) + \
                         0.2 + 0.075 * (self.species.reproduction_rate - 1)
            if random.random() <= birth_prob:
                if self.model.schedule.steps % 100 > 90:
                    self.make_ant("queen")
                else:
                    self.make_ant("worker")

        free_surrounding_cells = set(self.surrounding_cells) & self.model.grid.empties
        if (self.ants_inside or self.queens_inside) and free_surrounding_cells:
            if self.ants_inside:
                ant = self.ants_inside[0]
            else:
                ant = self.queens_inside[0]
            if list(ant.smell_cells_for("food trail", self.surrounding_cells)):
                self.release_ant()
            elif self.model.schedule.steps % 30 < 2:
                self.release_ant()


class AntsWorld(Model):
    def __init__(self, N_food_sites, N_obstacles, width, height, food_spawn, **kwargs):
        super().__init__()
        self.food_spawn = food_spawn
        self.N_obstacles = N_obstacles
        self.N_food_sites = N_food_sites
        self.grid = SingleGrid(width, height, False)
        self.schedule = RandomActivation(self)
        self.pheromone_map = Grid(width, height, False)
        for x in range(width):
            for y in range(height):
                self.pheromone_map[x][y] = defaultdict(lambda: 0)
        species_list = []
        for x in range(len(list(kwargs)) // 3):
            if kwargs["include_{}".format(x)]:
                species_list.append(
                    Species(
                        kwargs["ant_size_{}".format(x)],
                        kwargs["reproduction_rate_{}".format(x)],
                        len(species_list)
                    )
                )

        self.data_collector = DataCollector(
            model_reporters={"Species {}".format(s_id): (lambda id: (lambda m: count_ants(m, id)))(s_id) for s_id in
                             range(len(species_list))}
        )

        # Create agents
        for species in species_list:
            pos = random.choice(list(self.grid.empties))
            ah = Anthill(self.next_id(), self, species, pos)
            self.spawn_object(ah, pos)
        for _ in range(self.N_food_sites):
            pos = random.choice(list(self.grid.empties))
            fs = FoodSite(self.next_id(), self, random.randrange(100), pos, 0)
            self.spawn_object(fs, pos)
        for _ in range(self.N_obstacles):
            pos = random.choice(list(self.grid.empties))
            obs = Obstacle(self.next_id(), self)
            self.spawn_object(obs, pos)

    def spawn_object(self, object, coordinates):
        self.schedule.add(object)
        self.grid.place_agent(object, coordinates)

    def evaporate_pheromone(self):
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                for k in self.pheromone_map[x][y].keys():
                    self.pheromone_map[x][y][k] = max(0, self.pheromone_map[x][y][k] - 1)

    def step(self):
        self.data_collector.collect(self)
        self.schedule.step()
        self.evaporate_pheromone()
        if self.schedule.steps % self.food_spawn == 0:
            pos = random.choice(list(self.grid.empties))
            fs = FoodSite(self.next_id(), self, random.randrange(100), pos, 0)
            self.spawn_object(fs, pos)
