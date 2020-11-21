import ant_agent
from mesa import Agent, Model
from mesa.space import *
from mesa.time import BaseScheduler, RandomActivation
from mesa.datacollection import DataCollector
from collections import defaultdict
import random
import time
import numpy as np

FOOD_SIZE_BIRTH_RATIO = 2  # food required to produce a new ant = FOOD_SIZE_BIRTH_RATIO * ant_size
FOOD_PER_FOOD_SITE = 300
SEND_FORAGING_PARTY_TURN = 30  # every SEND_FORAGING_PARTY_TURN turn some ants go looking for the food
FORAGING_SENDING_DURATION = 4  # duration of period when sending foraging ants
QUEEN_SEASON_DURATION = 5  # duration of season in which queens are born
QUEEN_SEASON_TURN = 60  # queen season happens every QUEEN_SEASON_TURN + QUEEN_SEASON_SPEC_DIFF * reproduction rate
QUEEN_SEASON_SPEC_DIFF = 20
FOOD_BIRTH_PROB = 0.02  # probability of an ant being born = FOOD_BIRTH_PROB * (
# (self.food_units - minimum_food) // self.birth_food) * self.species.reproduction_rate, line 136
ANTS_RELEASE_TURN = 2  # ants may be released every ANTS_RELEASE_TURN


# TODO colony decides whether to release ants based on food supplies
# TODO more fierce ants

def sign(x):
    if x == 0:
        return 0
    return x // abs(x)


def count_ants(model, species_id):
    species = list(filter(lambda x: x.id == species_id, model.species_list))[0]
    ants = [ah.worker_counter for ah in species.anthills]
    return sum(ants)


def count_food(model, species_id):
    species = list(filter(lambda x: x.id == species_id, model.species_list))[0]
    food = [ah.food_units for ah in species.anthills]
    return sum(food)


class Species:
    def __init__(self, ant_size, reproduction_rate, id):
        self.id = id
        self.reproduction_rate = reproduction_rate
        self.ant_size = ant_size
        self.energy_food = 100 / self.ant_size  # how much energy is restored by one food unit
        self.anthills = []


class Obstacle(Agent):
    def __init__(self, unique_id, model, pos):
        super().__init__(unique_id, model)
        self.pos = pos


class FoodSite(Agent):
    def __init__(self, unique_id, model, initial_food_units, pos, r_rate=0):
        super().__init__(unique_id, model)
        self.initial_food_units = initial_food_units
        self.food_units = initial_food_units
        self.rate = r_rate  # regeneration rate of food
        self.pos = pos

    def destroy(self):
        self.model.schedule.remove(self)
        self.model.grid.remove_agent(self)

    def step(self):
        self.food_units = min(self.food_units + self.rate, self.initial_food_units)
        self.food_units += self.rate
        for x, y in self.model.grid.iter_neighborhood(self.pos, moore=True):
            self.model.pheromone_map["food"][x][y] = 2
        if not self.food_units:
            self.destroy()


class Anthill(Agent):
    def __init__(self, unique_id, model, species, pos, food_units=100):
        super().__init__(unique_id, model)
        self.species = species
        self.food_units = food_units
        self.pos = pos
        self.worker_counter = 0
        self.ants_inside = []
        self.queens_inside = []
        self.surrounding_cells = self.model.grid.get_neighborhood(self.pos, moore=True)
        self.birth_food = self.species.ant_size * FOOD_SIZE_BIRTH_RATIO
        self.turn = 0

        species.anthills.append(self)

    def release_ant(self, pheromone_cells={}, forage=False):
        if self.queens_inside:
            ant = self.queens_inside.pop()
        else:
            ant = self.ants_inside.pop(0)
            ant.forage = forage

        possible_locations = list(set(self.surrounding_cells) & self.model.grid.empties)
        weights = [1] * len(possible_locations)
        if set(pheromone_cells) & self.model.grid.empties and not forage:
            possible_locations = list(set(pheromone_cells) & self.model.grid.empties)
            weights = [pheromone_cells[pl] for pl in possible_locations]

        ant.pos = random.choices(possible_locations, weights)[0]
        ant.orient = (ant.pos[0] - self.pos[0], ant.pos[1] - self.pos[1])
        self.model.grid.place_agent(ant, ant.pos)

    def make_ant(self, w_or_q):
        if w_or_q == "worker":
            self.food_units -= self.birth_food
            ant = ant_agent.Ant(self.model.next_id(), self.model, self.species, self.pos, self)
            self.worker_counter += 1
            self.ants_inside.append(ant)
        if w_or_q == "queen":
            self.food_units -= self.birth_food * 2
            ant = ant_agent.Queen(self.model.next_id(), self.model, self.species, self.pos, self)
            self.queens_inside.append(ant)
        self.model.schedule.add(ant)

    def destroy(self):
        self.species.anthills.remove(self)
        self.model.schedule.remove(self)
        self.model.grid.remove_agent(self)

    def step(self):
        self.turn += 1
        minimum_food = self.birth_food * 2 + self.worker_counter * self.species.ant_size

        if self.food_units < minimum_food and self.worker_counter == 0:
            self.destroy()
            return

        if self.food_units > minimum_food:
            queen_season = QUEEN_SEASON_TURN + QUEEN_SEASON_SPEC_DIFF * (5 - self.species.reproduction_rate)
            if self.turn % queen_season < QUEEN_SEASON_DURATION and self.turn > queen_season:
                self.make_ant("queen")

            birth_prob = FOOD_BIRTH_PROB * (
                    (self.food_units - minimum_food) // self.birth_food) * self.species.reproduction_rate
            if random.random() < birth_prob:
                self.make_ant("worker")

        free_surrounding_cells = set(self.surrounding_cells) & self.model.grid.empties
        if (self.ants_inside or self.queens_inside) and free_surrounding_cells:
            if self.ants_inside:
                ant = self.ants_inside[0]
            else:
                ant = self.queens_inside[0]

            pheromone_cells = ant.smell_cells_for("food trail", self.surrounding_cells)
            if list(pheromone_cells) and self.turn % ANTS_RELEASE_TURN == 0:
                self.release_ant(pheromone_cells=pheromone_cells)

            elif self.turn % SEND_FORAGING_PARTY_TURN < FORAGING_SENDING_DURATION \
                    and self.turn > SEND_FORAGING_PARTY_TURN:
                self.release_ant(forage=True)


class AntsWorld(Model):
    def __init__(self, N_food_sites, N_obstacles, width, height, food_spawn, **kwargs):
        super().__init__()
        self.food_spawn = food_spawn
        self.N_obstacles = N_obstacles
        self.N_food_sites = N_food_sites
        self.grid = SingleGrid(width, height, False)
        self.schedule = RandomActivation(self)
        self.pheromone_map = defaultdict(lambda: np.zeros((height, width)))
        self.species_list = []

        for i in range(len(list(kwargs)) // 3):
            if kwargs["include_{}".format(i)]:
                self.species_list.append(
                    Species(
                        ant_size=kwargs["ant_size_{}".format(i)],
                        reproduction_rate=kwargs["reproduction_rate_{}".format(i)],
                        id=i
                    )
                )
        species_id = [s.id for s in self.species_list]
        self.ants_collector = DataCollector(
            model_reporters={"Species {}".format(s_id): (lambda id: (lambda model: count_ants(model, id)))(s_id)
                             for s_id in species_id}
        )
        self.food_collector = DataCollector(
            model_reporters={"Species {}".format(s_id): (lambda id: (lambda model: count_food(model, id)))(s_id)
                             for s_id in species_id}
        )

        # Create agents
        for species in self.species_list:
            pos = random.choice(list(self.grid.empties))
            self.spawn_object(Anthill(self.next_id(), self, species, pos))
        for _ in range(self.N_food_sites):
            pos = random.choice(list(self.grid.empties))
            self.spawn_object(FoodSite(self.next_id(), self, random.randrange(FOOD_PER_FOOD_SITE), pos, 0))
        for _ in range(self.N_obstacles):
            pos = random.choice(list(self.grid.empties))
            self.spawn_object(Obstacle(self.next_id(), self, pos))

    def spawn_object(self, object):
        self.schedule.add(object)
        self.grid.place_agent(object, object.pos)

    def evaporate_pheromone(self):
        for k in self.pheromone_map.keys():
            self.pheromone_map[k][self.pheromone_map[k] > 0] -= 1

    def step(self):
        self.ants_collector.collect(self)
        self.food_collector.collect(self)
        start = time.time()
        self.schedule.step()
        print("schedule step = ", time.time()-start)
        start = time.time()
        self.evaporate_pheromone()
        print("evaporate_pheromone = ", time.time()-start)

        if self.food_spawn and self.schedule.steps % self.food_spawn == 0:
            pos = random.choice(list(self.grid.empties))
            self.spawn_object(FoodSite(self.next_id(), self, random.randrange(FOOD_PER_FOOD_SITE), pos, r_rate=0))
