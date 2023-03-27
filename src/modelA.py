from pyomo.environ import Set, ConcreteModel, Var, Constraint, Objective, minimize, maximize
from pyomo.environ import Binary, NonNegativeIntegers, NonNegativeReals
from pyomo.kernel import SolverFactory, value, SolverStatus
import logging

from .read_data import InputData

class ModelA:

    def __init__(self, input_data: InputData, month):
        self.data_input = input_data
        self.output_lp_file = True
        self.use_api_mode = True
        if self.use_api_mode:
            self.opt = SolverFactory('cplex_persistent')
        else:
            self.opt = SolverFactory('cplex_direct')
        # self.opt = SolverFactory('gurobi_persistent')
        self.model = ConcreteModel('Step1ContinuousModel')
        self.obj_dict = {}
        self.shelfNum = 10
        self.month = month

    def create_pyomo_sets(self):
        self.model.product_Set = Set(initialize=[p for p in self.data_input.products])
        logging.info("Created  self.model.product_Set: %s"%(len(self.model.product_Set)))

        self.model.rack_Set = Set(initialize=list(range(1, self.data_input.rack_num + 1)))
        logging.info("Created self.model.rack_Set: %s"%(len(self.model.rack_Set)))

        self.model.shelf_Set = Set(initialize=list(range(1, self.shelfNum+1)))
        logging.info('Created self.model.shelf_Set: %s'%(len(self.model.shelf_Set)))

        self.model.product_tray_Set = Set(initialize=[(p, i) for p, dmd_dict in self.data_input.demands.items()
                                           for i in range(dmd_dict[self.month])])
        logging.info("Created self.model.product_tray_Set: %s"%(len(self.model.product_tray_Set)))

    def build_vars(self):
        self.model.product_tray_rack_shelf_Set = Set(initialize=[
            (p, i, r, s) for (p, i) in self.model.product_tray_Set
            for r in self.model.rack_Set
            for s in self.model.shelf_Set
        ])
        logging.info("Created self.model.product_tray_rack_shelf_Set: %s"%(len(self.model.product_tray_rack_shelf_Set)))

        self.model.whether_product_tray_rack_shelf_var = Var(
            self.model.product_tray_rack_shelf_Set, name='whether_product_tray_rack_shelf_var', domain=Binary)
        logging.info('created whether_product_tray_rack_shelf_var: %s' % len(self.model.whether_product_tray_rack_shelf_var))

    def get_solution_dict(self):
        sol_dict = {}
        for k, v in self.model.component_map(ctype=Var).items():
            sol_dict[v.getname()] = {kk: vv() for kk, vv in v.items()}
        return sol_dict