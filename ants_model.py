import ant_agent
from mesa import Agent, Model
from mesa.space import *
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
from collections import defaultdict

ANT_SIZE_CARGO_RATIO = 5  # cargo = X * ant_size
SIZE_HEALTH_RATIO = 2  # ant_health = X * ant_size
SIZE_DAMAGE_RATIO = 1  # inflicted_damage = X * ant_size
FOOD_SIZE_BIRTH_RATIO = 2  # X * ant_size = food to produce a new ant
SIZE_SELF_PHEROMONE_RATIO = 20


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


class FoodSite(Agent):
    def __init__(self, unique_id, model, initial_food_units, coordinates, regeneration_rate=0):
        super().__init__(unique_id, model)
        self.initial_food_units = initial_food_units
        self.food_units = initial_food_units
        self.rate = regeneration_rate
        self.coordinates = coordinates

    def step(self):
        self.food_units = min(self.food_units + self.rate, self.initial_food_units)
        self.food_units += self.rate
        for x, y in self.model.pheromone_map.iter_neighborhood(self.coordinates, moore=True):
            self.model.pheromone_map[x][y]["food"] = 2
        if not self.food_units:
            self.model.schedule.remove(self)
            self.model.grid.remove_agent(self)


# class Queen(Ant):
#     def __init__(self, unique_id, model, species, size):
#         super().__init__(unique_id, model, species, size)


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
            ant = ant_agent.Ant(self.model.next_id(), self.model, self.species, self.coordinates, self, stays_inside)
            self.model.schedule.add(ant)
            self.model.grid.place_agent(ant, self.coordinates)


# TODO display number of ants
class AntsWorld(Model):
    def __init__(self, N_species, N_food_sites, width, height, ):
        super().__init__()
        self.N_food_sites = N_food_sites
        self.N_species = N_species
        self.grid = MultiGrid(width, height, False)
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
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            c = Colony(self.next_id(), self, Species(i + 1, i + 1, i), (x, y))
            self.schedule.add(c)
            self.grid.place_agent(c, (x, y))
        for _ in range(self.N_food_sites):
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            fs = FoodSite(self.next_id(), self, self.random.randrange(50), (x, y), 0 * self.random.random())
            self.schedule.add(fs)
            self.grid.place_agent(fs, (x, y))

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
