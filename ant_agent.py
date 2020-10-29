from mesa import Agent
import ants_model
from itertools import product

# from ants_model import Colony, FoodSite, Model, Species

ANT_SIZE_CARGO_RATIO = 5  # cargo = X * ant_size
SIZE_HEALTH_RATIO = 2  # ant_health = X * ant_size
SIZE_DAMAGE_RATIO = 1  # inflicted_damage = X * ant_size
SIZE_SELF_PHEROMONE_RATIO = 20


# TODO Foraging ants go more or less straight
# TODO Singular Grid
# TODO pheromone path
# TODO energy
# TODO colony stores ants, decides whether to release ants based on food supplies
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
        self.last_position = coordinates

    # just move to given cell
    def move(self, new_position):
        self.model.grid.move_agent(self, new_position)
        self.coordinates = new_position

    # get dictionary of objects in the 8-neighbourhood
    def sense_neighborhood(self):
        objects = {"enemies": [], "food": []}
        neighbors = self.model.grid.iter_neighbors(self.coordinates, moore=True)
        for neighbor in neighbors:
            if isinstance(neighbor, ants_model.FoodSite):
                objects["food"].append(neighbor)
            elif isinstance(neighbor, Ant) and neighbor.species.id != self.species.id:
                objects["enemies"].append(neighbor)
        return objects

    # attack given ant
    def attack(self, agent):
        agent.health -= self.size * SIZE_DAMAGE_RATIO

    # home going based on the self pheromone
    def go_home(self):
        back_path = self.smell_neighborhood_for(self)
        if back_path:
            new_position = self.random.choices(list(back_path), weights=back_path.values(), k=1)[0]
        else:
            possible_moves = self.model.pheromone_map.get_neighborhood(self.coordinates, moore=True)
            new_position = self.random.choice(possible_moves)
        self.last_position = self.coordinates
        self.move(new_position)

    def go_straight(self):

        dx = self.coordinates[0] - self.last_position[0]
        dy = self.coordinates[1] - self.last_position[1]
        new_pos = self.coordinates[0] + dx, self.coordinates[1] + dy
        first_neighborhood = set(self.model.grid.get_neighborhood(self.coordinates, moore=True))
        second_neighborhood = set(self.model.grid.get_neighborhood(new_pos, moore=False, include_center=True))
        possible_moves = list(first_neighborhood & second_neighborhood)
        if not possible_moves:
            possible_moves = self.model.grid.get_neighborhood(self.coordinates, moore=True)
            possible_moves.remove(self.last_position)
        move_weights = [8 if pos == new_pos else 1 for pos in possible_moves]
        return self.random.choices(possible_moves, move_weights, k=1)[0]
        # new_dx, new_dy = dx, dy
        # if new_dx == 0:
        #     new_dx = self.random.choices([-1, 0, 1], weights=[0.1, 0.8, 0.1])[0]
        # if new_dy == 0:
        #     new_dy = self.random.choices([-1, 0, 1], weights=[0.1, 0.8, 0.1])[0]
        # if abs(new_dx) and abs(new_dy):
        #     new_dx = self.random.choices([0, new_dx], weights=[0.2, 0.8])[0]
        # new_dy = self.random.choices([0, new_dy], weights=[0.2, 0.8])[0]
        #
        # return self.coordinates[0] + new_dx, self.coordinates[1] + new_dy

    # go in search for food, leave self-pheromone
    def go_forage(self):
        if self.last_position == self.coordinates:
            new_pos = self.random.choice(self.model.grid.get_neighborhood(self.coordinates, moore=True))
        elif list(self.smell_neighborhood_for("food")):
            new_pos = self.random.choice(list(self.smell_neighborhood_for("food")))
        else:
            new_pos = self.go_straight()
        self.last_position = self.coordinates
        self.move(new_pos)
        self.leave_pheromone(self, SIZE_SELF_PHEROMONE_RATIO)

    def leave_pheromone(self, smell, strength):
        x, y = self.coordinates
        self.model.pheromone_map[x][y][smell] += strength * self.size

    def smell_neighborhood_for(self, smell):
        smells = {}
        for x, y in self.model.pheromone_map.iter_neighborhood(self.coordinates, moore=True):
            if self.model.pheromone_map[x][y][smell] > 0:
                smells[(x, y)] = self.model.pheromone_map[x][y][smell]
        return smells

    # take food from the food_site
    def take_food(self, food_site) -> None:
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
            objects = self.sense_neighborhood()
            if objects["enemies"]:
                self.attack(objects["enemies"][0])
        elif self.cargo:
            if self.coordinates in self.model.grid.get_neighborhood(self.home_colony.coordinates, moore=True):
                self.leave_food(self.home_colony)
            else:
                self.go_home()
        else:
            objects = self.sense_neighborhood()
            if objects["enemies"]:
                self.attack(objects["enemies"][0])
            elif objects["food"]:
                self.take_food(objects["food"][0])
            else:
                self.go_forage()
