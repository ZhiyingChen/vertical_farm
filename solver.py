from src.read_data import InputData
from src.log_setup import setup_log
from src.modelA import ModelA
from src.utils import ProductInfoHeader, DemandHeader
from src.config import *

import time
import logging

if __name__ == '__main__':
    st = time.time()

    input_folder = 'dataSet'
    output_folder = 'output'
    setup_log(output_folder)
    try:
        input = InputData(input_folder, output_folder, rackNum=25)
        input.generate_data()

        modelA = ModelA(input, month='1')

        ed = time.time()
        logging.info('total running time: %s' % (ed - st))

    except BaseException as e:
        logging.error('run daily job fail:', exc_info=True)
        raise e