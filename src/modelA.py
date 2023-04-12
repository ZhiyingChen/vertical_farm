from pyomo.environ import Set, ConcreteModel, Var, Constraint, Objective, minimize, maximize
from pyomo.environ import Binary, NonNegativeIntegers, NonNegativeReals
from pyomo.kernel import SolverFactory, value, SolverStatus
import logging
import os


from .read_data import InputData
from .utils import ProductInfoHeader as pih
from .utils import Separator as sp
from .config import *

class ModelA:

    def __init__(self, input_data: InputData, rack_num, month):
        self.data_input = input_data
        self.output_lp_file = True
        self.use_api_mode = False
        if self.use_api_mode:
            self.opt = SolverFactory('cplex_persistent')
        else:
            self.opt = SolverFactory('cplex_direct')
        # self.opt = SolverFactory('gurobi_persistent')
        self.model = ConcreteModel('modelA')
        self.obj_dict = {}
        self.shelf_num = self.data_input.shelf_num
        self.rack_num = rack_num
        self.month = month

    def create_pyomo_sets(self):
        self.model.product_Set = Set(initialize=[p for p in self.data_input.products])
        logging.info("Created  self.model.product_Set: %s"%(len(self.model.product_Set)))

        self.model.rack_Set = Set(initialize=list(range(1, self.rack_num + 1)))
        logging.info("Created self.model.rack_Set: %s"%(len(self.model.rack_Set)))

        self.model.shelf_Set = Set(initialize=list(range(1, self.shelf_num+1)))
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

    def build_one_rack_shelf_one_tray_constrs(self):
        def one_rack_shelf_one_tray_rule(model, p, i):
            return sum(self.model.whether_product_tray_rack_shelf_var[p, i, r, s] for r in self.model.rack_Set for s in
                       self.model.shelf_Set) == 1

        self.model.one_rack_shelf_one_tray_contrs = Constraint(self.model.product_tray_Set, rule=one_rack_shelf_one_tray_rule)
        logging.info('created one_rack_shelf_one_tray_contrs: %s' % len(self.model.one_rack_shelf_one_tray_contrs))

    def build_month_day_limit_constrs(self):
        self.model.rack_shelf_Set = Set(initialize=[(r, s) for r in self.model.rack_Set for s in self.model.shelf_Set])
        logging.info("Created  self.model.rack_shelf_Set: %s"%(len( self.model.rack_shelf_Set)))
        def month_day_limit_rule(model, r, s):
            return sum(
                self.data_input.products[p][pih.cycleLen] * self.model.whether_product_tray_rack_shelf_var[p, i, r, s]
                for (p, i) in self.model.product_tray_Set) <= self.data_input.month_days[self.month]

        self.model.month_day_limit_contrs = Constraint(self.model.rack_shelf_Set,
                                                               rule=month_day_limit_rule)
        logging.info('created month_day_limit_contrs: %s' % len(self.model.month_day_limit_contrs))

    def build_model(self):
        self.create_pyomo_sets()
        self.build_vars()

        self.build_one_rack_shelf_one_tray_constrs()
        self.build_month_day_limit_constrs()
        if self.use_api_mode:
            self.opt.set_instance(self.model)
    def solve_maximize_freq_benefit_obj(self):
        obj = sum(
            (self.shelf_num + 1 - s) * self.data_input.products[p][pih.waterFreq] *
            self.model.whether_product_tray_rack_shelf_var[p, i, r, s] for
            (p, i, r, s) in
            self.model.product_tray_rack_shelf_Set)

        if isinstance(obj, int):
            return True

        try:
            self.model.del_component(self.model.obj)
        except AttributeError:
            pass

        logging.info('start solve_maximize_freq_benefit_obj')
        self.model.obj = Objective(expr=obj, sense=maximize)
        log_file = self.data_input.output_folder + sp.splitStr + 'solve_maximize_freq_benefit_obj.log'

        if self.use_api_mode:
            self.opt.set_objective(self.model.obj)
            res = self.opt.solve(self.model, tee=True, logfile=log_file, warmstart=True,options=FREQ_OBJ_CPLEX_PARAMS)

        else:
            res = self.opt.solve(self.model, tee=True, logfile=log_file, warmstart=True,symbolic_solver_labels=False,
                                 options=FREQ_OBJ_CPLEX_PARAMS)
        self.log_opt_solve_info(log_file)
        solved = False
        if res.solver.status in [SolverStatus.ok, SolverStatus.aborted]:
            solved = True
            logging.info('finished solve_maximize_freq_benefit_obj: %s' % value(self.model.obj))
            self.obj_dict['maximize_freq_benefit_obj'] = value(self.model.obj)

        return solved
    @staticmethod
    def log_opt_solve_info(log_file):
        if os.path.exists(log_file):
            f = open(log_file)
            lines = f.readlines()
            for l in lines:
                logging.info(l.strip("\n"))
            f.close()
            os.remove(log_file)

    def get_solution_dict(self):
        sol_dict = {}
        for k, v in self.model.component_map(ctype=Var).items():
            sol_dict[v.getname()] = {kk: vv() for kk, vv in v.items()}
        return sol_dict

