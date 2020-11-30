from ants_model import *
from mesa.batchrunner import BatchRunner
from mesa.visualization.UserParam import UserSettableParameter
import pandas
width = height = 50
MAX_N_SPECIES = 4

labels = ["Species {}".format(s_id) for s_id in range(MAX_N_SPECIES)]

fixed_params = {
    "N_food_sites": 30,
    "N_obstacles": 100,
    "width": width,
    "height": height,
    "food_spawn": 10,
    "torus": True,
}
fixed_params.update({
    "include_0": True,
    "reproduction_rate_0": 4,
    "ant_size_0": 4
})
variable_params = {}
for i in range(1, MAX_N_SPECIES):
    variable_params.update(
        {"include_{}".format(i): [True],
         "reproduction_rate_{}".format(i): [3],
         "ant_size_{}".format(i): [3]})

batch_run = BatchRunner(AntsWorld,
                        variable_params,
                        fixed_params,
                        iterations=80,
                        max_steps=1500,
                        model_reporters={"ants": lambda m: [len(species.anthills) for species in m.species_list],
                                         "turn": lambda m: m.schedule.steps})
batch_run.run_all()
data_collector_agents = batch_run.get_model_vars_dataframe()
data_collector_agents.to_excel("ant_0_is_strongest_others_strong.xlsx")
