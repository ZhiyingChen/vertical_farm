import pandas as pd
import logging
from collections import defaultdict
from .config import *
from .log_setup import setup_log

class InputData:
    def __init__(self, input_folder, output_folder, rackNum, shelfNum):
        setup_log('../output', section_name='VerticalFarm')
        self.input_folder = input_folder
        self.output_folder = output_folder
        self.products = dict()
        self.demands = dict()
        self.month_days = dict()
        self.rack_num = rackNum
        self.shelf_num = shelfNum

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

    def generate_data(self):
        self.products = self.read_product_info()
        self.demands = self.read_demand()
        self.month_days = self.generate_month_days()


if __name__ == '__main__':

    input_folder = 'dataSet'
    output_folder = 'output'
    input = InputData(input_folder, output_folder)
    input.generate_data()


