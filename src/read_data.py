import pandas as pd
import logging
from collections import defaultdict
from .config import *
from .log_setup import setup_log
from .utils import ProductInfoHeader as pih

class MonthInfo:
    def __init__(self, rackNum, month):
        self.rack_num = rackNum
        self.month = month
        self.wBot_num = None
        self.lBot_num = None
        self.month_income = None
        self.month_supposed_income = None

    def __repr__(self):
        return "MonthInfo(rackNum = %s, month = %s)" % (self.rack_num, self.month)


class InputData:
    def __init__(self, input_folder, output_folder, shelfNum):
        setup_log('../output', section_name='VerticalFarm')
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.wBot_slot_length = 120
        self.lBot_slot_length = 180
        self.wBot_slots_num = 8
        self.lBot_slots_num = 5
        self.products = dict()
        self.demands = dict()
        self.month_days = dict()
        self.month_supposed_income = dict()
        self.shelf_num = shelfNum
        self.rack_light_round_duration = dict()
        self.rack_water_round_duration = dict()
        self.month_rack_sol_dict = defaultdict(dict)

    def read_product_info(self):
        from .utils import ProductInfoHeader as ph
        product_df = pd.read_csv(self.input_folder + PRODUCT_INFO_FILE, index_col=ph.product)
        product_dict = defaultdict(dict)
        for idx, r in product_df.iterrows():
            product_dict[idx] = r.to_dict()
        logging.info("Finished reading demands: %s" % (len(product_dict)))
        return product_dict

    def read_demand(self):
        from .utils import DemandHeader as dh
        demand_df = pd.read_csv(self.input_folder + DEMAND_FILE, index_col=dh.product)
        demand_dict = dict()
        for idx, r in demand_df.iterrows():
            demand_dict[idx] = r.to_dict()
        logging.info("Finished reading demands: %s"%(len(demand_dict)))
        return demand_dict

    def generate_month_days(self):
        month_days = {
            '1': 31,
            '2': 28,
            '3': 31,
            '4': 30,
            '5': 31,
            '6': 30,
            '7': 31,
            '8': 31,
            '9': 30,
            '10': 31,
            '11': 30,
            '12': 31
        }
        logging.info("Finished generating month_days.")
        return month_days

    def generate_supposed_income(self):
        month_supposed_income = dict()
        for product, month_demand in self.demands.items():
            for month, dmd_num in month_demand.items():
                curr_income = month_supposed_income.get(month, 0)
                income = self.products[product][pih.ProfitPerShelf] * dmd_num
                month_supposed_income[month] = curr_income + income
        return month_supposed_income
    def generate_data(self):
        self.products = self.read_product_info()
        self.demands = self.read_demand()
        self.month_days = self.generate_month_days()
        self.month_supposed_income = self.generate_supposed_income()


if __name__ == '__main__':

    input_folder = 'dataSet'
    output_folder = 'output'
    input = InputData(input_folder, output_folder)
    input.generate_data()


