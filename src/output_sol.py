import pandas as pd
import logging
from collections import defaultdict
import numpy as np
from math import ceil
from .read_data import InputData, MonthInfo
from .utils import ProductInfoHeader as pih
from .utils import String
from .BFD import Bin, Pack
class OutputSol:

    def __init__(self, modelA_solution_dict: dict, data_input: InputData, rack_num, month):
        self.waterMinPerL = 1.5
        self.lightMinPerLux = 2500
        self.climbDur = 10
        self.modelA_solution_dict = modelA_solution_dict
        self.modelB_solution_dict = dict()
        self.data_input = data_input
        self.rack_num = rack_num
        self.month = month
        self.plant_sol = self.modelA_solution_dict.get('whether_product_tray_rack_shelf_var', dict())
        self.plant_tray_pos_dict = dict()
        self.rack_shelf_plant_dict = dict()
        self.rack_shelf_plant_first_day_dict = dict()
        self.rack_shelf_round_dict = dict()
        self.rack_water_round_duration = dict()
        self.rack_light_round_duration = dict()
        self.wBot_num = 0
        self.lBot_num = 0


    # region generate modelA solution
    def generate_product_rack_arrangement(self):
        plant_ser = pd.Series(self.plant_sol)
        plant_ser = plant_ser[plant_ser > 1e-4]

        # Record each tray of the plant should be placed in which position
        plant_tray_pos_dict = dict()     # {(plant, tray): (rack, shelf)}
        # Record what plant should be put on each shelf of the rack
        rack_shelf_plant_dict = defaultdict(dict)   # {rack: {shelf: [(plant, tray, cycleLen, waterFrequency)]}}

        for (p, i, r, s), row in plant_ser.iteritems():
            plant_tray_pos_dict[(p, i)] = (r, s)
            rack_shelf_plant_dict[r][s] = rack_shelf_plant_dict[r].get(s, []) + [
                (p, i, self.data_input.products[p][pih.cycleLen], self.data_input.products[p][pih.waterFreq])]

        # Sort rack_shelf_plant_dict by cycle length
        updated_rack_shelf_plant_dict = defaultdict(dict)
        for rack_num, shelf_plant_dict in rack_shelf_plant_dict.items():
            for shelf_level, plant_lt in shelf_plant_dict.items():
                sorted_plant_lt = sorted(plant_lt, key=lambda x: (x[3], x[2], x[0], x[1]), reverse=True)
                updated_rack_shelf_plant_dict[rack_num][shelf_level] = sorted_plant_lt
        logging.info("Finish generating plant_tray_pos_dict and rack_shelf_plant_dict.")
        return plant_tray_pos_dict, updated_rack_shelf_plant_dict

    def generate_first_day_arrangement(self):
        # Record what plant should be put on each shelf of the rack on the first day of this month
        rack_shelf_plant_first_day_dict = defaultdict(dict)  # {rack: {shelf: (plant, tray, cycleLen, waterFrequency)}}

        for r in range(1, self.rack_num + 1):
            for s in range(1, self.data_input.shelf_num + 1):
                if s not in self.rack_shelf_plant_dict[r]:
                    rack_shelf_plant_first_day_dict[r][s] = (String.empty, 0, 0, 0)
                else:
                    rack_shelf_plant_first_day_dict[r][s] = self.rack_shelf_plant_dict[r][s][0]
        logging.info("Finish generating rack_shelf_plant_first_day_dict.")
        return rack_shelf_plant_first_day_dict

    def generate_rack_shelf_round(self):
        # Record how many times a robot should climb to this shelf level
        rack_shelf_round_dict = defaultdict(dict) # {rack: {shelf: round}}
        for r in range(1, self.rack_num + 1):
            for s in range(1, self.data_input.shelf_num + 1):
                if s < self.data_input.shelf_num:
                    max_s_plus_1_above = max(
                        self.rack_shelf_plant_first_day_dict[r][_s][-1] for _s in range(s+1, self.data_input.shelf_num + 1))
                else:
                    max_s_plus_1_above = 0
                rack_shelf_round_dict[r][s] = self.rack_shelf_plant_first_day_dict[r][s][-1] - max_s_plus_1_above
        logging.info("Finish generating rack_shelf_round_dict.")
        return rack_shelf_round_dict

    def generate_water_duration_bar(self):
        # Record the water duration of all rounds in each rack
        rack_water_round_duration = defaultdict(dict)  # {rack: [round1, round2, round3, ...]}
        for rack, round_dict in self.rack_shelf_round_dict.items():
            round_duration = []
            for shelf_level, round_num in round_dict.items():
                if round_num <= 1e-4:
                    continue
                # round duration equals climbing time plus watering time of each shelf level
                round_dur = self.climbDur * (shelf_level - 1) + sum(
                    self.data_input.products[self.rack_shelf_plant_first_day_dict[rack][s][0]].get(pih.waterEach, 0)
                    for s in range(1, shelf_level + 1))
                round_duration.extend(int(round_num) * [round(round_dur)])
            rack_water_round_duration[rack] = round_duration
        logging.info("Finish generating rack_water_round_duration.")
        return rack_water_round_duration

    def generate_light_duration_bar(self):
        # Record the top shelf level of each rack
        top_shelf_level = {}  # {rack: top_shelf_level}
        for rack, shelf_plant in self.rack_shelf_plant_first_day_dict.items():
            top_level = self.data_input.shelf_num
            for shelf_level in range(1, self.rack_num + 1):
                plant_above_shelf_level = {plant[0] for s, plant in shelf_plant.items() if s > shelf_level}
                if len(plant_above_shelf_level) == 1 and String.empty in plant_above_shelf_level:
                    top_level = shelf_level
                    break
            top_shelf_level[rack] = top_level

        # Record the light duration in each rack (only one round for each rack)
        # rack_light_round_duration = {rack: light_duration}
        # light duration equals climbing time plus lighting time of each shelf level
        rack_light_round_duration = {
            rack: round((top_shelf_level.get(rack, 1) - 1) * self.climbDur + sum(
                    self.data_input.products[self.rack_shelf_plant_first_day_dict[rack][s][0]].get(pih.luxTotal, 0) / self.lightMinPerLux
                    for s in range(1, top_shelf_level.get(rack, 0) + 1)))
            for rack in range(1, self.rack_num + 1)
        }
        logging.info("Finish generating rack_light_round_duration.")
        return rack_light_round_duration
    def generate_income(self):

        monthInfo = MonthInfo(rackNum=self.rack_num, month=self.month)
        # actual income
        income = 0
        for rack, shelf_plant_dict in self.rack_shelf_plant_dict.items():
            for shelf_level, plant_lt in shelf_plant_dict.items():
                income += sum(self.data_input.products[plant[0]].get(pih.pricePerShelf, 0) for plant in plant_lt)
        monthInfo.month_income = income

        # supposed_income
        monthInfo.month_supposed_income = self.data_input.month_supposed_income.get(self.month, 0)
        self.data_input.month_rack_sol_dict[self.rack_num][self.month] = monthInfo
    def generate_modelA_sol(self):
        self.plant_tray_pos_dict, self.rack_shelf_plant_dict = self.generate_product_rack_arrangement()
        self.rack_shelf_plant_first_day_dict = self.generate_first_day_arrangement()
        self.rack_shelf_round_dict = self.generate_rack_shelf_round()
        self.rack_water_round_duration = self.generate_water_duration_bar()
        self.rack_light_round_duration = self.generate_light_duration_bar()
        self.data_input.rack_water_round_duration = self.rack_water_round_duration
        self.data_input.rack_light_round_duration = self.rack_light_round_duration
        self.generate_income()

    # endregion

    # region generate modelB solution
    def get_robot_num(self):
        self.wBot_num = sum(v for k, v in self.modelB_solution_dict.get('whether_wBot_var', dict()).items())
        self.lBot_num = sum(v for k, v in self.modelB_solution_dict.get('whether_lBot_var', dict()).items())
        monthInfo = self.data_input.month_rack_sol_dict[self.rack_num][self.month]
        monthInfo.wBot_num = self.wBot_num
        monthInfo.lBot_num = self.lBot_num

        logging.info("wBot_num: %s, lBot_num: %s"%(self.wBot_num, self.lBot_num))

    # endregion

    # region generate BFD solution
    def generate_robot_num_by_BFD(self):
        # wBotNum
        wBot_rounds = [round_dur for rack, round_dur_lt in self.rack_water_round_duration.items()
                       for round_dur in round_dur_lt if round_dur > 1e-4]
        water_Pack = Pack(values=wBot_rounds, maxVal=self.data_input.wBot_slot_length)
        wBot_slots = water_Pack.BFDPack()
        self.wBot_num = ceil(len(wBot_slots) / self.data_input.wBot_slots_num)

        # lBotNum
        lBot_rounds = [round_dur for rack, round_dur in self.rack_light_round_duration.items()
                       if round_dur > 1e-4]
        light_Pack = Pack(values=lBot_rounds, maxVal=self.data_input.lBot_slot_length)
        lBot_slots = light_Pack.BFDPack()
        self.lBot_num = ceil(len(lBot_slots) / self.data_input.lBot_slots_num)

        monthInfo = self.data_input.month_rack_sol_dict[self.rack_num][self.month]
        monthInfo.wBot_num = self.wBot_num
        monthInfo.lBot_num = self.lBot_num

        logging.info("wBot_num: %s, lBot_num: %s" % (self.wBot_num, self.lBot_num))
        logging.info("Finish generate_robot_num_by_BFD.")
    # endregion