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


class Colony(Agent):
    def __init__(self, unique_id, model, species: Species, coordinates):
        super().__init__(unique_id, model)
        self.species = species
        self.food_units = 10
        self.coordinates = coordinates
        self.ants_inside = []
        self.turn_counter = 0

    def release_ant(self):
        ant = self.ants_inside.pop()

        ant_coordinates = self.random.choice(
            list(
                filter(lambda c: self.model.grid.is_cell_empty(c),
                       self.model.grid.get_neighborhood(self.coordinates, moore=True))
            )
        )
        ant.coordinates = ant_coordinates
        ant_orientation = (ant_coordinates[0] - self.coordinates[0], ant_coordinates[1] - self.coordinates[1])
        ant.orientation = ant_orientation
        self.model.grid.place_agent(ant, ant_coordinates)

    def step(self):
        # self.food_units -= self.ants_inside * self.species.ant_size
        self.turn_counter += 1

        spawn_ant = self.turn_counter // self.species.base_reproduction_rate
        self.turn_counter %= self.species.base_reproduction_rate
        if spawn_ant and self.food_units > FOOD_SIZE_BIRTH_RATIO * self.species.ant_size:
            self.food_units -= self.species.ant_size * FOOD_SIZE_BIRTH_RATIO
            ant = ant_agent.Ant(self.model.next_id(), self.model, self.species, self.coordinates, self)
            self.ants_inside.append(ant)
            self.model.schedule.add(ant)

        if self.ants_inside and list(
                filter(lambda c: self.model.grid.is_cell_empty(c),
                       self.model.grid.get_neighborhood(self.coordinates, moore=True))
        ):
            self.release_ant()


class AntsWorld(Model):
    def __init__(self, N_species, N_food_sites, width, height, ):
        super().__init__()
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
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            while not self.grid.is_cell_empty((x, y)):
                x = self.random.randrange(self.grid.width)
                y = self.random.randrange(self.grid.height)
            c = Colony(self.next_id(), self, Species(i + 1, i + 10, i), (x, y))
            self.schedule.add(c)
            self.grid.place_agent(c, (x, y))
        for _ in range(self.N_food_sites):
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            while not self.grid.is_cell_empty((x, y)):
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
