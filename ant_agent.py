from mesa import Agent
import ants_model
from itertools import product

# from ants_model import Colony, FoodSite, Model, Species

ANT_SIZE_CARGO_RATIO = 5  # cargo = X * ant_size
SIZE_HEALTH_RATIO = 2  # ant_health = X * ant_size
SIZE_DAMAGE_RATIO = 1  # inflicted_damage = X * ant_size
SIZE_PHEROMONE_RATIO = 20
SELF_PHEROMONE_RATIO = 50


# TODO pheromone path
# TODO energy
# TODO colony decides whether to release ants based on food supplies
class Ant(Agent):
    def __init__(self, unique_id, model, species, coordinates, home_colony):
        super().__init__(unique_id, model)
        self.home_colony = home_colony
        self.size = species.ant_size
        self.health = self.size * SIZE_HEALTH_RATIO
        self.coordinates = coordinates
        self.species = species
        self.cargo = 0
        self.last_position = coordinates
        self.orientation = None

    def update_orientation(self):
        self.orientation = (self.coordinates[0] - self.last_position[0],
                            self.coordinates[1] - self.last_position[1])

    # Move to the given cell if it is empty if not do nothing. Returns whether move was done.
    def move(self, new_position):
        if self.model.grid.is_cell_empty(new_position):
            self.last_position = self.coordinates
            self.model.grid.move_agent(self, new_position)
            self.coordinates = new_position
            return True
        return False

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
        moves, weights = self.find_straight_path_points("wide")  # narrow possibly is better, but problem at food site
        new_pos = self.random.choice(moves)

        food_trail = self.smell_cells_for("food trail", moves)
        if list(food_trail):
            new_pos = self.random.choices(list(food_trail), weights=food_trail.values(), k=1)[0]
        else:
            self_trail = self.smell_cells_for(self, moves)
            if self_trail:
                new_pos = self.random.choices(list(self_trail), weights=self_trail.values(), k=1)[0]

        self_moved = self.move(new_pos)
        if self_moved:
            self.leave_pheromone("food trail", SIZE_PHEROMONE_RATIO)

    def go_forage(self):
        moves, weights = self.find_straight_path_points("wide")
        if list(self.smell_cells_for("food", moves)):
            new_pos = self.random.choice(list(self.smell_cells_for("food", moves)))

        elif list(self.smell_cells_for("food trail", moves)):
            free_cells = list(filter(self.model.grid.is_cell_empty, self.smell_cells_for("food trail", moves)))
            if free_cells:
                new_pos = self.random.choice(free_cells)
            else:

                new_pos = self.random.choices(moves, weights, k=1)[0]

        else:
            if moves:
                new_pos = self.random.choices(moves, weights, k=1)[0]
            else:
                new_pos = self.choose_random_path()
        self.move(new_pos)
        self.leave_pheromone(self, SELF_PHEROMONE_RATIO)

    def choose_random_path(self):
        moves = self.model.grid.get_neighborhood(self.coordinates, moore=True)
        moves.remove(self.last_position)
        return self.random.choice(moves)

    # Finds more or less straight path based on intersection of current neighborhood and the neighborhood of
    # the next point that lies in the direction the ant is going. If no such points then take random except
    # the last position
    def find_straight_path_points(self, w_or_n):
        next_point = self.coordinates[0] + self.orientation[0], self.coordinates[1] + self.orientation[1]
        if w_or_n == "wide":
            first_neighborhood = set(
                self.model.grid.get_neighborhood(self.coordinates, moore=True, include_center=False))
            second_neighborhood = set(
                self.model.grid.get_neighborhood(self.last_position, moore=False, include_center=True))
            possible_moves = list(first_neighborhood - second_neighborhood)

        elif w_or_n == "narrow":
            first_neighborhood = set(
                self.model.grid.get_neighborhood(self.coordinates, moore=True, include_center=False))
            second_neighborhood = set(
                self.model.grid.get_neighborhood(next_point, moore=False, include_center=True))
            possible_moves = list(first_neighborhood & second_neighborhood)

        move_weights = [8 if pos == next_point else 1 for pos in possible_moves]
        return possible_moves, move_weights

    # go in search for food, leave self-pheromone

    def leave_pheromone(self, smell, strength):
        x, y = self.coordinates
        self.model.pheromone_map[x][y][smell] += strength * self.size

    def smell_cells_for(self, smell, cells):
        smells = {}
        for x, y in cells:
            if self.model.pheromone_map[x][y][smell] > 0:
                smells[(x, y)] = self.model.pheromone_map[x][y][smell]
        return smells

    def turn_around(self):
        self.last_position[0] += self.orientation[0]
        self.last_position[1] += self.orientation[1]

    # take food from the food_site
    def take_food(self, food_site):
        self.cargo = min(self.size * ANT_SIZE_CARGO_RATIO, food_site.food_units)
        food_site.food_units -= self.cargo
        self.turn_around()

    # leave food at the colony
    def leave_food(self, colony):
        colony.food_units += self.cargo
        self.cargo = 0
        self.turn_around()

    # just die
    def die(self):
        self.model.schedule.remove(self)
        self.model.grid.remove_agent(self)

    def step(self):
        if self.health <= 0:
            self.die()
        elif self.coordinates == self.home_colony.coordinates:
            pass
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

        self.update_orientation()
