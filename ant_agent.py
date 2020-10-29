from mesa import Agent

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
        self.last_position = None

    # just move to given cell
    def move(self, new_position: Tuple[int, int]):
        self.model.grid.move_agent(self, new_position)
        self.coordinates = new_position

    # get dictionary of objects in the 8-neighbourhood
    def check_neighbours(self):
        objects = {"enemies": [], "food": []}
        neighbors = self.model.grid.iter_neighbors(self.coordinates, moore=True)
        for neighbor in neighbors:
            if isinstance(neighbor, FoodSite):
                objects["food"].append(neighbor)
            elif isinstance(neighbor, Ant) and neighbor.species.id != self.species.id:
                objects["enemies"].append(neighbor)
        return objects

    # attack given ant
    def attack(self, agent):
        agent.health -= self.size * SIZE_DAMAGE_RATIO

    # home going based on the self pheromone
    def go_home(self):
        back_path = self.scan_neighborhood_for(self)
        if back_path:
            new_position = self.random.choices(list(back_path), weights=back_path.values(), k=1)[0]
        else:
            possible_moves = self.model.pheromone_map.get_neighborhood(self.coordinates, moore=True)
            new_position = self.random.choice(possible_moves)
        self.last_position = self.coordinates
        self.move(new_position)

    # go in search for food, leave self-pheromone
    def go_forage(self):
        possible_moves = list(self.scan_neighborhood_for("food"))
        if not possible_moves:
            possible_moves = self.model.grid.get_neighborhood(self.coordinates, moore=True)
        new_x, new_y = self.random.choice(possible_moves)
        self.move((new_x, new_y))
        self.leave_pheromone(self, SIZE_SELF_PHEROMONE_RATIO)

    def leave_pheromone(self, smell, strength):
        x, y = self.coordinates
        self.model.pheromone_map[x][y][smell] += strength * self.size

    def scan_neighborhood_for(self, smell):
        smells = {}
        for x, y in self.model.pheromone_map.iter_neighborhood(self.coordinates, moore=True):
            if self.model.pheromone_map[x][y][smell] > 0:
                smells[(x, y)] = self.model.pheromone_map[x][y][smell]
        return smells

    # take food from the food_site
    def take_food(self, food_site: FoodSite) -> None:
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
            objects = self.check_neighbours()
            if objects["enemies"]:
                self.attack(objects["enemies"][0])
        elif self.cargo:
            if self.coordinates in self.model.grid.get_neighborhood(self.home_colony.coordinates, moore=True):
                self.leave_food(self.home_colony)
            else:
                self.go_home()
        else:
            objects = self.check_neighbours()
            if objects["enemies"]:
                self.attack(objects["enemies"][0])
            elif objects["food"]:
                self.take_food(objects["food"][0])
            else:
                self.go_forage()
