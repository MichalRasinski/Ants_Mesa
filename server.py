from ants_model import *
from ant_agent import *
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import PieChartModule

from mesa.visualization.UserParam import UserSettableParameter

width = height = 50
MAX_N_OBJECTS = width * height // 3
MAX_N_SPECIES = 4


def agent_portrayal(agent):
    if isinstance(agent, Ant):
        portrayal = {"Shape": "circle",
                     "Filled": "true",
                     "Layer": 1,
                     "Color": colours[agent.species.id],
                     "r": agent.size * 0.5}
        if isinstance(agent, Queen):
            portrayal["Filled"] = "false"
            portrayal["r"] = agent.size

    elif type(agent) is Anthill:
        portrayal = {"Shape": "circle",
                     "Filled": "true",
                     "Layer": 1,
                     "Color": colours[agent.species.id],
                     "r": agent.species.ant_size,
                     "text": "f:{0:.0f}/a:{1:.0f}".format(agent.food_units, agent.worker_counter),
                     "text_color": "black"}

    elif type(agent) is FoodSite:
        portrayal = {"Shape": "rect",
                     "w": 0.9,
                     "h": 0.9,
                     "Filled": "True",
                     "Layer": 1,
                     "text": "{0:.0f}".format(agent.food_units),
                     "Color": "SandyBrown"}
    elif type(agent) is Obstacle:
        portrayal = {"Shape": "rect",
                     "w": 0.9,
                     "h": 0.9,
                     "Filled": "true",
                     "Layer": 0,
                     "Color": "Gray"}

    return portrayal


colours = ["red", "DarkOrchid", "Chartreuse", "aqua", "orange"]
labels = ["Species {}".format(s_id) for s_id in range(MAX_N_SPECIES)]

model_params = {
    "N_food_sites": UserSettableParameter("slider", "Spots with Food",
                                          value=10, min_value=0, max_value=100, step=10),
    "N_obstacles": UserSettableParameter("slider", "Obstacles", value=100, min_value=0,
                                         max_value=MAX_N_OBJECTS, step=50),
    "width": width,
    "height": height,
    "food_spawn": UserSettableParameter("slider", "Food spawns every x-th turn",
                                        value=10, min_value=0, max_value=20),
    "torus": UserSettableParameter("checkbox", "Map is toroidal", value=True),
    "species_text": UserSettableParameter('static_text', value="")
}
for i in range(MAX_N_SPECIES):
    model_params.update(
        {"include_{}".format(i): UserSettableParameter(
            "checkbox", "Include Species {}".format(i), True if i <= 1 else False)})
    model_params.update({"reproduction_rate_{}".format(i): UserSettableParameter(
        "slider", "Reproduction Rate of the Species {}".format(i), value=3, min_value=1, max_value=5)})
    model_params.update({"ant_size_{}".format(i): UserSettableParameter(
        "slider", "Ant Size of the Species {}".format(i), value=3, min_value=1, max_value=5)})

world = CanvasGrid(agent_portrayal, width, height, 600, 600)
chart_ants = PieChartModule(
    [{"Label": label, "Color": colour} for label, colour in zip(labels, colours)],
    canvas_height=250,
    canvas_width=300,
    data_collector_name='ants_collector'
)

server = ModularServer(AntsWorld,
                       [world, chart_ants],
                       "Ants World",
                       model_params)
server.port = 8521
