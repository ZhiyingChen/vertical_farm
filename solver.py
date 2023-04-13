from src.read_data import InputData, MonthInfo
from src.log_setup import setup_log
from src.modelA import ModelA
from src.modelA import *
from src.modelB import ModelB
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

        input = InputData(input_folder, output_folder, shelfNum=shelfNum)
        input.generate_data()

        rackNumLt = [i**2 for i in range(5, 15)]

        for rackNum in rackNumLt:
            for month in range(1, 13):
                month = str(month)

                logging.info("Begin solving problems for rack %s, month %s" % (rackNum, month))
                modelA = ModelA(input, rack_num=rackNum, month='1')
                modelA.build_model()
                modelA.solve_maximize_freq_benefit_obj()
                modelA_solution_dict = modelA.get_solution_dict()

                pickle_dump(input.output_folder + '/modelA_sol_rack_{}_month_{}.pkl'.format(rackNum, month),
                            modelA_solution_dict)
                modelA_solution_dict = pickle_load(
                    input.output_folder + '/modelA_sol_rack_{}_month_{}.pkl'.format(rackNum, month))

                outputSol = OutputSol(modelA_solution_dict, input, rack_num=rackNum, month=month)
                outputSol.generate_modelA_sol()

                modelB = ModelB(input, rack_num=rackNum)
                modelB.build_model()
                modelB.solve_minimize_robot_num_obj()
                modelB_solution_dict = modelB.get_solution_dict()

                pickle_dump(input.output_folder + '/modelB_sol_rack_{}_month_{}.pkl'.format(rackNum, month),
                            modelB_solution_dict)
                modelB_solution_dict = pickle_load(
                    input.output_folder + '/modelB_sol_rack_{}_month_{}.pkl'.format(rackNum, month))

                outputSol.modelB_solution_dict = modelB_solution_dict
                outputSol.get_robot_num()

        ed = time.time()
        logging.info('total running time: %s' % (ed - st))

    except BaseException as e:
        logging.error('run daily job fail:', exc_info=True)
        raise e