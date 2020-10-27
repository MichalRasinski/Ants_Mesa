from mesa import Agent, Model
from mesa.space import *
from mesa.time import RandomActivation


class Species:
    def __init__(self, ant_size, base_reproduction_rate, id):
        self.id = id
        self.base_reproduction_rate = base_reproduction_rate
        self.ant_size = ant_size


class Ant(Agent):
    def __init__(self, unique_id, model, species, size, coordinates, home_coord, stays_inside):
        super().__init__(unique_id, model)
        self.stays_inside = stays_inside
        self.home_coord = home_coord
        self.health = size
        self.coordinates = coordinates
        self.species = species
        self.size = size

    def move(self, dx=None, dy=None):
        if dx or dy:
            new_position = self.coordinates[0] - dx, self.coordinates[1] - dy
        else:
            possible_steps = self.model.grid.get_neighborhood(
                self.coordinates,
                moore=True)
            new_position = self.random.choice(possible_steps)

        enemy_ant = self.search_for_enemies(new_position)
        if enemy_ant:
            self.attack(enemy_ant)
        else:
            self.model.grid.move_agent(self, new_position)
            self.coordinates = new_position

    # check if a cell is occupied and attack enemy ants
    def search_for_enemies(self, position):
        x, y = position
        if any(self.model.grid[x][y]):
            for agent in self.model.grid[x][y]:
                if isinstance(agent, Ant) and agent.species.id != self.species.id:
                    return agent
        return None

    def attack(self, agent):
        agent.health -= self.size

    def go_back(self):
        dx, dy = self.home_coord - self.coordinates
        move_x = self.random.choice(0, dx / abs(dx))
        move_y = self.random.choice(0, dy / abs(dy))
        self.move(move_x, move_y)

    def step(self):
        if self.health <= 0:
            self.model.schedule.remove(self)
            self.model.grid.remove_agent(self)
        elif self.stays_inside:
            pass
        else:
            self.move()


# class WorkerAnt(Ant):
#     def __init__(self, unique_id, model, species, size, coordinates, home_coord):
#         super().__init__(self, unique_id, model, species, size, coordinates, home_coord)


# class HomeAnt(Ant):
#     def __init__(self, unique_id, model, species, size, coordinates, home_coord):
#         super().__init__(self, unique_id, model, species, size, coordinates, home_coord)


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
            stays_inside = self.random.random() > 0.3
            ant = Ant(self.model.next_id(), self.model, self.species, self.species.ant_size, self.coordinates,
                      self.coordinates, stays_inside)
            self.model.schedule.add(ant)
            self.model.grid.place_agent(ant, self.coordinates)


class FoodSite(Agent):
    def __init__(self, unique_id, model, initial_food_units, regeneration_rate=0):
        super().__init__(unique_id, model)
        self.initial_food_units = initial_food_units
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
            c = Colony(self.next_id(), self, Species(i + 1, i + 1, i), (x, y))
            self.schedule.add(c)
            self.grid.place_agent(c, (x, y))
        for i in range(2 * self.num_species):
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            fs = FoodSite(self.next_id(), self, self.random.randrange(100), regeneration_rate=2 * self.random.random())
            self.schedule.add(fs)
            self.grid.place_agent(fs, (x, y))

    def step(self):
        self.schedule.step()
