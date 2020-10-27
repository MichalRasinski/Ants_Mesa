from ants_model import *
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer


def agent_portrayal(agent):
    colours = ["blue", "black", "red"]
    if isinstance(agent, Ant):
        portrayal = {"Shape": "circle",
                     "Filled": "true",
                     "Layer": 0,
                     "Color": colours[agent.species.id],
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


width = height = 20
map = CanvasGrid(agent_portrayal, width, height)
server = ModularServer(AntsWorld,
                       [map],
                       "Ants World",
                       {"N_species": 3, "width": width, "height": height})
server.port = 8521  # The default
server.launch()
