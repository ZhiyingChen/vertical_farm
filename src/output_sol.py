import pandas as pd
from collections import defaultdict
from src.read_data import InputData
class OutputSol:

    def __init__(self, solution_dict: dict, data_input: InputData):
        self.solution_dict = solution_dict
        self.data_input = data_input
        self.plant_sol = self.solution_dict.get('whether_product_tray_rack_shelf_var', dict())
        self.plant_tray_pos_dict = dict()
        self.rack_shelf_plant_dict = dict()
    def generate_product_rack_arrangement(self):
        plant_ser = pd.Series(self.plant_sol)
        plant_ser = plant_ser[plant_ser > 1e-4]

        # Record each tray of the plant should be placed in which position
        plant_tray_pos_dict = dict()     # {(plant, tray): (rack, shelf)}
        # Record what plant should be put on each shelf of the rack
        rack_shelf_plant_dict = defaultdict(dict)   # {rack: {shelf: [(plant, tray)]}}

        for (p, i, r, s), row in plant_ser.iteritems():
            plant_tray_pos_dict[(p, i)] = (r, s)
            rack_shelf_plant_dict[r][s] = rack_shelf_plant_dict[r][s] + [(p, i)]

        return plant_tray_pos_dict, rack_shelf_plant_dict

