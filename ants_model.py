from mesa import Agent, Model
from mesa.space import *
from mesa.time import RandomActivation
import math


class Species:
    def __init__(self, ant_size, base_reproduction_rate, id):
        self.id = id
        self.base_reproduction_rate = base_reproduction_rate
        self.ant_size = ant_size


class Ant(Agent):
    def __init__(self, unique_id, model, species, size, coordinates):
        super().__init__(unique_id, model)
        self.health = size
        self.coordinates = coordinates
        self.species = species
        self.size = size

    def move(self):
        possible_steps = self.model.grid.get_neighborhood(
            self.coordinates,
            moore=True)
        new_position = self.random.choice(possible_steps)
        if self.field_is_safe(new_position):
            self.model.grid.move_agent(self, new_position)
            self.coordinates = new_position

    def field_is_safe(self, position):
        x, y = position
        if any(self.model.grid[x][y]):
            for agent in self.model.grid[x][y]:
                if isinstance(agent, Ant) and agent.species.id != self.species.id:
                    print("Attack")
                    self.attack(agent)
                    return False
        return True

    def attack(self, agent):
        agent.health -= self.size


class WorkerAnt(Ant):
    def __init__(self, unique_id, model, species, size, coordinates):
        super().__init__(unique_id, model, species, size, coordinates)

    def step(self):
        if self.health <= 0:
            self.model.schedule.remove(self)
            self.model.grid.remove_agent(self)
        else:
            self.move()


class Queen(Ant):
    def __init__(self, unique_id, model, species, size):
        super().__init__(unique_id, model, species, size)

    def step(self):
        if self.health <= 0:
            self.model.schedule.remove(self)
            self.model.grid.remove_agent(self)
        self.move()


class Colony(Agent):
    def __init__(self, unique_id, model, species: Species, coordinates: tuple):
        super().__init__(unique_id, model)
        self.species = species
        self.food_units = 100
        self.coordinates = coordinates
        self.ants_inside = 0
        self.turn_counter = 0

    def step(self):
        self.food_units -= self.ants_inside * self.species.ant_size
        self.turn_counter += 1
        ants_to_spawn = self.turn_counter // self.species.base_reproduction_rate
        if ants_to_spawn and self.food_units > 2 * self.species.ant_size:
            self.food_units -= 2 * self.species.ant_size
            self.turn_counter -= self.species.base_reproduction_rate
            ant = WorkerAnt(self.model.next_id(), self.model, self.species, self.species.ant_size, self.coordinates)
            self.model.schedule.add(ant)
            self.model.grid.place_agent(ant, self.coordinates)


class FoodSite(Agent):
    def __init__(self, unique_id, model, initial_food_units, coordinates, regeneration_rate=0):
        super().__init__(unique_id, model)
        self.initial_food_units = initial_food_units
        self.coordinates = coordinates
        self.food_units = initial_food_units
        self.rate = regeneration_rate

    def step(self):
        self.food_units = min(self.food_units + self.rate, self.initial_food_units)


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
            c = Colony(self.next_id(), self, Species(i+1, i + 1, i), (x, y))
            self.schedule.add(c)
            self.grid.place_agent(c, (x, y))
        for i in range(2 * self.num_species):
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            fs = FoodSite(self.next_id(), self, self.random.randrange(100), (x, y),
                          regeneration_rate=2 * self.random.random())
            self.schedule.add(fs)
            self.grid.place_agent(fs, (x, y))

    def step(self):
        self.schedule.step()
