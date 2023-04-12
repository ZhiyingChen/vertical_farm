DEMAND_FILE = '/demandTrays.csv'
PRODUCT_INFO_FILE = '/productSet.csv'

FREQ_OBJ_CPLEX_PARAMS = {'timelimit': 300, 'mip_tolerances_mipgap': 0.05, 'emphasis_mip': 4, 'preprocessing_symmetry': 1,
                         'mip_strategy_heuristicfreq': 5, 'mip_strategy_presolvenode': 0}
FREQ_OBJ_RELAX = 0.1