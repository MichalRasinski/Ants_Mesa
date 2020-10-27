from ants_model import *
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.modules import ChartModule

# TODO text of food inside colony

colours = ["blue", "black", "red"]


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


N_species = 3
width = height = 30

labels = ["Species {}".format(s_id) for s_id in range(N_species)]

chart = ChartModule(
    [{"Label": label, "Color": colour} for label, colour in zip(labels, colours)],
    data_collector_name='data_collector'
)
map = CanvasGrid(agent_portrayal, width, height)
server = ModularServer(AntsWorld,
                       [map, chart],
                       "Ants World",
                       {"N_species": N_species, "width": width, "height": height})
server.port = 8521  # The default
server.launch()
