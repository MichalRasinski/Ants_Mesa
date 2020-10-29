from ants_model import *
from ant_agent import *
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import ChartModule
import random
# TODO text of food inside colony

N_species = 3
N_food_sites = 10
width = height = 10

colours = ["#" + ''.join([random.choice('0123456789ABCDEF') for j in range(6)])
           for i in range(N_species)]
labels = ["Species {}".format(s_id) for s_id in range(N_species)]


def agent_portrayal(agent):
    if isinstance(agent, Ant):
        portrayal = {"Shape": "circle",
                     "Filled": "true",
                     "Layer": 0,
                     "Color": colours[agent.species.id],
                     "r": 0.5}
        if agent.cargo > 0:
            portrayal = {"Shape": "circle",
                         "Filled": "false",
                         "Layer": 0,
                         "Color": "green",
                         "r": 0.5}
    elif type(agent) is Colony:
        portrayal = {"Shape": "circle",
                     "Filled": "true",
                     "Layer": 0,
                     "Color": colours[agent.species.id],
                     "r": 2.0}
    elif type(agent) is FoodSite:
        portrayal = {"Shape": "rect",
                     "w": 1.5,
                     "h": 1.5,
                     "Filled": "true",
                     "Layer": 0,
                     "Color": "Yellow"}
    return portrayal


chart = ChartModule(
    [{"Label": label, "Color": colour} for label, colour in zip(labels, colours)],
    data_collector_name='data_collector'
)
map = CanvasGrid(agent_portrayal, width, height)
server = ModularServer(AntsWorld,
                       [map, chart],
                       "Ants World",
                       {"N_species": N_species, "N_food_sites": N_food_sites, "width": width, "height": height})
server.port = 8521  # The default
server.launch()
