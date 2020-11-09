from mesa import Agent
import ants_model
from itertools import product
import numpy as np
import random

ANT_SIZE_CARGO_RATIO = 5  # cargo = X * ant_size
SIZE_HEALTH_RATIO = 2  # ant_health = X * ant_size
SIZE_DAMAGE_RATIO = 1  # inflicted_damage = X * ant_size
SIZE_PHEROMONE_RATIO = 40
SELF_PHEROMONE_RATIO = 80
MAX_PHEROMONE_STRENGTH = 100


# TODO colony decides whether to release ants based on food supplies
# TODO follow the path
class Ant(Agent):
    def __init__(self, unique_id, model, species, pos, anthill):
        super().__init__(unique_id, model)
        self.anthill = anthill
        self.size = species.ant_size
        self.health = self.size * SIZE_HEALTH_RATIO
        self.pos = pos
        self.species = species
        self.cargo = 0
        self.last_pos = pos
        self.energy = 100
        self.orientation = None
        self.forage = False
        self.lost = False
        self.pheromone_strength = 0

    def update_orientation(self):
        self.orientation = (self.pos[0] - self.last_pos[0], self.pos[1] - self.last_pos[1])

    def neighborhood(self, number):
        if number == 8:
            return self.model.grid.get_neighborhood(self.pos, moore=True, include_center=False)
        if number == 4:
            return self.model.grid.get_neighborhood(self.pos, moore=False, include_center=False)

    # Move to the given cell if it is empty if not do nothing. Returns whether move was done.
    def move(self, new_position):
        self.last_pos = self.pos
        self.model.grid.move_agent(self, new_position)
        self.pos = new_position
        self.update_orientation()
        if self.cargo and not self.lost:
            self.leave_pheromone("food trail", self.pheromone_strength)

    # get dictionary of objects in the 8-neighbourhood
    def sense_neighborhood(self):
        objects = {"enemies": [], "food": []}
        for neighbor in self.model.grid.iter_neighbors(self.pos, moore=True, include_center=False):
            if isinstance(neighbor, ants_model.FoodSite):
                objects["food"].append(neighbor)
            elif isinstance(neighbor, Ant) and neighbor.species.id != self.species.id:
                objects["enemies"].append(neighbor)
        return objects

    # attack given ant
    def attack(self, agent):
        agent.health -= self.size * SIZE_DAMAGE_RATIO

    def go_forage(self):
        moves = self.find_straight_path_points("narrow")
        empty_cells = set(moves) & self.model.grid.empties
        if not empty_cells:
            moves = self.find_straight_path_points("wide")
            empty_cells = set(moves) & self.model.grid.empties
            if not empty_cells:
                self.turn_around()
                return

        weights = self.weigh_straight_path_points(empty_cells)
        new_pos = random.choices(list(empty_cells), weights, k=1)[0]
        self.move(new_pos)

    def go_random(self):
        moves = self.find_straight_path_points("wide")
        moves = list(set(moves) & self.model.grid.empties)
        if moves:
            weights = self.weigh_straight_path_points(moves, w=4)
            self.move(random.choices(moves, weights)[0])

    def go_down_the_trail(self, pheromone):
        destiny_cell = None
        moves = self.find_straight_path_points("wide")
        empty_cells = set(moves) & self.model.grid.empties
        if not empty_cells:
            self.turn_around()
            return

        trail = self.smell_cells_for(pheromone, moves)
        destiny_cell = "occupied" if list(trail) else None
        empty_trail_cells = list(set(trail) & empty_cells)

        if empty_trail_cells:
            farthest_move = sorted(empty_trail_cells,
                                   key=lambda x: abs(x[0] - self.pos[0]) + abs(x[1] - self.pos[1]),
                                   reverse=True)[0]
            destiny_cell = farthest_move
        # move to a cell adjacent to the smell cell
        else:
            possible_trail_moves = []
            for trail_cell in list(trail):
                possible_trail_moves += self.model.grid.get_neighborhood(trail_cell, moore=False)
            possible_trail_moves = list(set(possible_trail_moves) & empty_cells)
            if possible_trail_moves:
                destiny_cell = random.choice(possible_trail_moves)

        if destiny_cell == "occupied":
            pass
        elif destiny_cell:
            self.move(destiny_cell)
        else:
            self.turn_around()
            self.lost = True

    # Finds more or less straight path based on intersection of current neighborhood and other neighborhood
    def find_straight_path_points(self, w_or_n):
        first_neighborhood = set(self.neighborhood(8))

        if w_or_n == "wide":  # 3 cells in front
            second_neighborhood = set(self.model.grid.get_neighborhood(self.last_pos, moore=False, include_center=True))
            possible_moves = list(first_neighborhood - second_neighborhood)

        elif w_or_n == "narrow":  # 3 cells in front + 2 cells at sides
            next_point = self.pos[0] + self.orientation[0], self.pos[1] + self.orientation[1]
            second_neighborhood = set(self.model.grid.get_neighborhood(next_point, moore=False, include_center=True))
            possible_moves = list(first_neighborhood & second_neighborhood)

        return possible_moves

    def weigh_straight_path_points(self, moves, w=6):
        next_point = self.pos[0] + self.orientation[0], self.pos[1] + self.orientation[1]
        move_weights = [w if pos == next_point else 1 for pos in moves]
        return move_weights

    def leave_pheromone(self, smell, strength):
        x, y = self.pos
        self.model.pheromone_map[x][y][smell] = min(self.model.pheromone_map[x][y][smell] + strength * self.size,
                                                    MAX_PHEROMONE_STRENGTH)

    def smell_cells_for(self, smell, cells):
        smells = {}
        for x, y in cells:
            if self.model.pheromone_map[x][y][smell] > 0:
                smells[(x, y)] = self.model.pheromone_map[x][y][smell]
        return smells

    def turn_around(self):
        self.last_pos = self.pos[0] + self.orientation[0], self.pos[1] + self.orientation[1]
        self.update_orientation()

    # take food from the food_site
    def take_food(self, food_site):
        self.cargo = min(self.size * ANT_SIZE_CARGO_RATIO, food_site.food_units)
        food_site.food_units -= self.cargo
        self.pheromone_strength = food_site.food_units / 3
        self.leave_pheromone("food trail", self.pheromone_strength)
        self.turn_around()

    def enter_anthill(self):
        self.anthill.food_units += self.cargo
        self.cargo = 0
        self.lost = False
        self.forage = False
        self.model.grid.remove_agent(self)
        self.anthill.ants_inside.append(self)

    def eat(self):
        e_diff = 100 - self.energy
        to_eat = min(e_diff / self.species.food_energy, self.anthill.food_units)
        self.energy += to_eat * self.species.food_energy
        self.anthill.food_units -= to_eat

    # just die
    def die(self):
        self.model.schedule.remove(self)
        if self in self.anthill.ants_inside:
            self.anthill.ants_inside.remove(self)
        else:
            self.model.grid.remove_agent(self)

    def step(self):
        # height = self.model.pheromone_map.height
        # food_trails = [[self.model.pheromone_map[x][y]["food trail"] for x in range(height)] for y in
        #                range(height - 1, -1, -1)]
        # food_trails = np.array(food_trails)
        if self.health <= 0 or not self.energy:
            self.die()
            return
        elif self in self.anthill.ants_inside:
            if self.energy < 80:
                self.eat()
            return

        self.energy -= 1
        self.leave_pheromone(self, SELF_PHEROMONE_RATIO)

        objects = self.sense_neighborhood()
        if objects["enemies"]:
            self.attack(objects["enemies"][0])
        elif objects["food"] and not self.cargo:
            self.take_food(objects["food"][0])
        elif self.cargo:
            if self.pos in self.anthill.surrounding_cells:
                self.enter_anthill()
            else:
                self.go_down_the_trail(self)
        elif self.forage:
            self.go_forage()
        elif self.lost:
            if self.pos in self.anthill.surrounding_cells:
                self.enter_anthill()
            else:
                food_trail = self.smell_cells_for("food trail", self.find_straight_path_points("wide"))
                self_trail = self.smell_cells_for("food trail", self.find_straight_path_points("wide"))

                if list(food_trail):
                    self.go_down_the_trail("food trail")
                elif list(self_trail):
                    self.go_down_the_trail(self)
                else:
                    self.go_random()
        else:
            self.go_down_the_trail("food trail")
