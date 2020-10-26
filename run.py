from ants_model import *
from mesa.visualization.modules import CanvasGrid
from mesa.visualization.ModularVisualization import ModularServer


def agent_portrayal(agent):
    colours = ["blue", "black", "red"]
    if type(agent) is WorkerAnt:
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


model = AntsWorld(3, 20, 20)
map = CanvasGrid(agent_portrayal, 50, 50)
server = ModularServer(AntsWorld,
                       [map],
                       "Ants World",
                       {"N_species": 3, "width": 50, "height": 50})
server.port = 8521  # The default
server.launch()
