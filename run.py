from ants_model import *
from ant_agent import *
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import ChartModule
from mesa.visualization.UserParam import UserSettableParameter

import random

# TODO text of food inside colony

MAX_N_SPECIES = 5
width = height = 50
MAX_N_OBJECTS = width * height / 3


def agent_portrayal(agent):
    if isinstance(agent, Ant):
        portrayal = {"Shape": "circle",
                     "Filled": "false",
                     "Layer": 1,
                     "Color": colours[agent.species.id],
                     "r": agent.size * 0.0,
                     "text": agent.unique_id,
                     "text_color": colours[agent.species.id]}
        if agent.forage:
            portrayal["text_color"] = "brown"
        if agent.cargo:
            portrayal["text_color"] = "green"
        if agent.lost:
            portrayal["text_color"] = "red"
            if agent.cargo:
                portrayal["text_color"] = "yellow"
    elif type(agent) is Anthill:
        portrayal = {"Shape": "circle",
                     "Filled": "true",
                     "Layer": 1,
                     "Color": colours[agent.species.id],
                     "r": agent.species.ant_size}
    elif type(agent) is FoodSite:
        portrayal = {"Shape": "rect",
                     "w": 1,
                     "h": 1,
                     "Filled": "true",
                     "Layer": 1,
                     "Color": "Yellow"}
    elif type(agent) is Obstacle:
        portrayal = {"Shape": "rect",
                     "w": 1,
                     "h": 1,
                     "Filled": "true",
                     "Layer": 1,
                     "Color": "Black"}

    return portrayal


model_params = {
    "N_food_sites": UserSettableParameter("number", "Initial Number of Spots with Food", 50, 0, MAX_N_OBJECTS),
    "N_obstacles": UserSettableParameter("number", "Number of Obstacles", 50, 0, MAX_N_OBJECTS),
    "width": width,
    "height": height
}
for i in range(MAX_N_SPECIES):
    model_params.update(
        {"include_{}".format(i): UserSettableParameter("checkbox", "Include species {}".format(i), False)})
    model_params.update({"reproduction_rate_{}".format(i): UserSettableParameter(
        "slider", "Reproduction Rate of Species {}".format(i), value=1, min_value=1, max_value=3, step=0.1)})
    model_params.update({"ant_size_{}".format(i): UserSettableParameter(
        "slider", "Ant Size of Species {}".format(i), value=1, min_value=1, max_value=3, step=0.1)})

colours = ["#" + ''.join([random.choice('0123456789ABCDEF') for j in range(6)])
           for i in range(MAX_N_SPECIES)]
labels = ["Species {}".format(s_id) for s_id in range(MAX_N_SPECIES)]

map = CanvasGrid(agent_portrayal, width, height, 600, 600)
chart = ChartModule(
    [{"Label": label, "Color": colour} for label, colour in zip(labels, colours)],
    data_collector_name='data_collector'
)
server = ModularServer(AntsWorld,
                       [map, chart],
                       "Ants World",
                       model_params)
server.port = 8521  # The default
server.launch()
