from src.read_data import InputData
from src.log_setup import setup_log
from src.modelA import ModelA
from src.modelA import *
from src.utils import ProductInfoHeader, DemandHeader
from src.config import *
from src.function import pickle_dump, pickle_load
from src.output_sol import OutputSol
import time
import logging

if __name__ == '__main__':
    st = time.time()

    input_folder = 'dataSet'
    output_folder = 'output'
    setup_log(output_folder)
    shelfNum = 10


    try:
        rackNum = 25
        input = InputData(input_folder, output_folder, rackNum=rackNum, shelfNum=shelfNum)
        input.generate_data()

        month = '1'
        modelA = ModelA(input, month='1')
        modelA.build_model()
        modelA.solve_maximize_freq_benefit_obj()
        modelA_solution_dict = modelA.get_solution_dict()

        pickle_dump(input.output_folder + '/modelA_sol_rack_{}_month_{}.pkl'.format(rackNum, month),
                    modelA_solution_dict)
        modelA_solution_dict = pickle_load(
            input.output_folder + '/modelA_sol_rack_{}_month_{}.pkl'.format(rackNum, month))

        outputSol = OutputSol(modelA_solution_dict, input)
        outputSol.generate_modelA_sol()

        ed = time.time()
        logging.info('total running time: %s' % (ed - st))

    except BaseException as e:
        logging.error('run daily job fail:', exc_info=True)
        raise e