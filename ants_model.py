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
SELF_PHEROMONE_RATIO = 50


# killed ant produces pheromone crying for help
# killed ant is a source of food
# starving ant may ask for food another ant

def sign(x):
    if x == 0:
        return 0
    else:
        return x // abs(x)


def count_ants(model, species_id):
    ants = filter(lambda x: isinstance(x, ant_agent.Ant) and x.species.id == species_id, model.schedule.agents)
    return len(list(ants))


class Species:
    def __init__(self, ant_size, base_reproduction_rate, id):
        self.id = id
        self.base_reproduction_rate = base_reproduction_rate
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
    def __init__(self, unique_id, model, species: Species, coordinates):
        super().__init__(unique_id, model)
        self.species = species
        self.food_units = 10
        self.pos = coordinates
        self.ants_inside = []
        self.turn_counter = 0
        self.surrounding_cells = self.model.grid.get_neighborhood(self.pos, moore=True)

    def release_ant(self):
        ant = self.ants_inside.pop()
        pheromone_cells = ant.smell_cells_for("food trail", self.surrounding_cells)
        possible_locations = list(set(self.surrounding_cells) & self.model.grid.empties)
        weights = [1 for pl in possible_locations]
        ant.forage = False
        if self.turn_counter % 30 < 2:
            ant.forage = True

        if set(pheromone_cells) & self.model.grid.empties:
            ant.forage = False
            possible_locations = list(set(pheromone_cells) & self.model.grid.empties)
            weights = [pheromone_cells[pl] for pl in possible_locations]
        ant.coordinates = random.choices(possible_locations, weights)[0]
        ant.orientation = (ant.coordinates[0] - self.pos[0], ant.coordinates[1] - self.pos[1])
        self.model.grid.place_agent(ant, ant.coordinates)

    def step(self):
        # self.food_units -= self.ants_inside * self.species.ant_size
        spawn_ant = False
        self.turn_counter += 1
        free_surrounding_cells = set(self.surrounding_cells) & self.model.grid.empties
        if self.turn_counter % self.species.base_reproduction_rate == 0:
            spawn_ant = True
        if spawn_ant and self.food_units > FOOD_SIZE_BIRTH_RATIO * self.species.ant_size:
            self.food_units -= self.species.ant_size * FOOD_SIZE_BIRTH_RATIO
            ant = ant_agent.Ant(self.model.next_id(), self.model, self.species, self.pos, self)
            self.ants_inside.append(ant)
            self.model.schedule.add(ant)

        if self.ants_inside and free_surrounding_cells:
            ant = self.ants_inside[0]
            print(list(ant.smell_cells_for("food trail", self.surrounding_cells)))

            if list(ant.smell_cells_for("food trail", self.surrounding_cells)):
                print(list(ant.smell_cells_for("food trail", self.surrounding_cells)))
                self.release_ant()
            elif self.turn_counter % 30 < 2:
                self.release_ant()


class AntsWorld(Model):
    def __init__(self, N_species, N_food_sites, N_obstacles, width, height):
        super().__init__()
        self.N_obstacles = N_obstacles
        self.N_food_sites = N_food_sites
        self.N_species = N_species
        self.grid = SingleGrid(width, height, False)
        self.schedule = RandomActivation(self)
        self.pheromone_map = Grid(width, height, False)
        for x in range(width):
            for y in range(height):
                self.pheromone_map[x][y] = defaultdict(lambda: 0)
        self.data_collector = DataCollector(
            model_reporters={"Species {}".format(s_id): (lambda id: (lambda m: count_ants(m, id)))(s_id) for s_id in
                             range(self.N_species)}
        )
        # Create agents
        for i in range(self.N_species):
            x, y = random.choice(list(self.grid.empties))
            c = Anthill(self.next_id(), self, Species(i + 1, i + 10, i), (x, y))
            self.schedule.add(c)
            self.grid.place_agent(c, (x, y))
        for _ in range(self.N_food_sites):
            x, y = random.choice(list(self.grid.empties))
            fs = FoodSite(self.next_id(), self, random.randrange(150), (x, y), random.choice([0, 2]))
            self.schedule.add(fs)
            self.grid.place_agent(fs, (x, y))
        for _ in range(self.N_obstacles):
            x, y = random.choice(list(self.grid.empties))
            obs = Obstacle(self.next_id(), self)
            self.grid.place_agent(obs, (x, y))

    def step(self):
        self.data_collector.collect(self)
        self.schedule.step()
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                for k in self.pheromone_map[x][y].keys():
                    self.pheromone_map[x][y][k] = max(0, self.pheromone_map[x][y][k] - 1)

    # def get_colonies(self):
    #     colonies = filter(lambda x: isinstance(x, Colony), self.schedule.agents)
    #     colonies_by_species = defaultdict(list)
    #     for colony in colonies:
    #         colonies_by_species[colony.species.id].append(colony)
    #     return colonies_by_species
