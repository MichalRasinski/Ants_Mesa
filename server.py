from ants_model import *
from ant_agent import *
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import ChartModule
from mesa.visualization.UserParam import UserSettableParameter

import random

width = height = 50
MAX_N_OBJECTS = width * height / 3
MAX_N_SPECIES = 5


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
        # "text": agent.unique_id,
        # "text_color": colours[agent.species.id]}
        # if agent.forage:
        #     portrayal["text_color"] = "brown"
        # if agent.cargo:
        #     portrayal["text_color"] = "green"
        # if agent.lost:
        #     portrayal["text_color"] = "red"
        #     if agent.cargo:
        #         portrayal["text_color"] = "yellow"
    elif type(agent) is Anthill:
        portrayal = {"Shape": "circle",
                     "Filled": "true",
                     "Layer": 1,
                     "Color": colours[agent.species.id],
                     "r": agent.species.ant_size,
                     "text": "{0:.0f}".format(agent.food_units),
                     "text_color": "black"}

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
    "height": height,
    "food_spawn": UserSettableParameter("slider", "Food Site spawns every x turns", value=5, min_value=1, max_value=10),
    "species_text": UserSettableParameter('static_text', value="Below parameters controlling ant species")
}
for i in range(MAX_N_SPECIES):
    model_params.update(
        {"include_{}".format(i): UserSettableParameter(
            "checkbox", "Include Species {}".format(i), True if i <= 1 else False)})
    model_params.update({"reproduction_rate_{}".format(i): UserSettableParameter(
        "slider", "Reproduction Rate of the Species {}".format(i), value=3, min_value=1, max_value=5)})
    model_params.update({"ant_size_{}".format(i): UserSettableParameter(
        "slider", "Ant Size of the Species {}".format(i), value=3, min_value=1, max_value=5)})

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
