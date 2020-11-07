from ants_model import *
from ant_agent import *
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import ChartModule
from mesa.visualization.UserParam import UserSettableParameter

import random

# TODO text of food inside colony

MAX_N_SPECIES = 10
width = height = 50
MAX_N_OBJECTS = width * height / 3


def agent_portrayal(agent):
    if isinstance(agent, Ant):
        portrayal = {"Shape": "circle",
                     "Filled": "false",
                     "Layer": 1,
                     "Color": colours[agent.species.id],
                     "r": agent.size * 0.5}
        if agent.forage:
            portrayal["Color"] = "brown"
        if agent.cargo:
            portrayal["Color"] = "green"
        if agent.lost:
            portrayal["Color"] = "red"
            if agent.cargo:
                portrayal["Color"] = "yellow"
    elif type(agent) is Anthill:
        portrayal = {"Shape": "circle",
                     "Filled": "true",
                     "Layer": 0,
                     "Color": colours[agent.species.id],
                     "r": agent.species.ant_size}
    elif type(agent) is FoodSite:
        portrayal = {"Shape": "rect",
                     "w": 1,
                     "h": 1,
                     "Filled": "true",
                     "Layer": 0,
                     "Color": "Yellow"}
    elif type(agent) is Obstacle:
        portrayal = {"Shape": "rect",
                     "w": 1,
                     "h": 1,
                     "Filled": "true",
                     "Layer": 0,
                     "Color": "Black"}
    return portrayal


model_params = {
    "N_species": UserSettableParameter("slider", "Number of Competing Colonies", 1, 1, MAX_N_SPECIES),
    "N_food_sites": UserSettableParameter("number", "Initial Number of Spots with Food", 15, 0, MAX_N_OBJECTS),
    "N_obstacles": UserSettableParameter("number", "Number of Obstacles", 15, 0, MAX_N_OBJECTS),
    "width": width,
    "height": height
}
colours = ["#" + ''.join([random.choice('0123456789ABCDEF') for j in range(6)])
           for i in range(MAX_N_SPECIES)]
labels = ["Species {}".format(s_id) for s_id in range(MAX_N_SPECIES)]

map = CanvasGrid(agent_portrayal, width, height)
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
