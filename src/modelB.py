from pyomo.environ import Set, ConcreteModel, Var, Constraint, Objective, minimize, maximize
from pyomo.environ import Binary, NonNegativeIntegers, NonNegativeReals
from pyomo.kernel import SolverFactory, value, SolverStatus
import logging
import os
from math import ceil

from .read_data import InputData
from .utils import ProductInfoHeader as pih
from .utils import Separator as sp
from .config import *

class ModelB:

    def __init__(self, input_data: InputData, rack_num):
        self.data_input = input_data
        self.output_lp_file = True
        self.use_api_mode = False
        if self.use_api_mode:
            self.opt = SolverFactory('cplex_persistent')
        else:
            self.opt = SolverFactory('cplex_direct')
        # self.opt = SolverFactory('gurobi_persistent')
        self.model = ConcreteModel('modelB')
        self.obj_dict = {}
        self.wBot_slot_length = self.data_input.wBot_slot_length
        self.lBot_slot_length = self.data_input.lBot_slot_length
        self.wBot_slots_num = self.data_input.wBot_slots_num
        self.lBot_slots_num = self.data_input.lBot_slots_num
        self.rack_num = rack_num
        self.rack_water_round_duration = self.data_input.rack_water_round_duration
        self.rack_light_round_duration = self.data_input.rack_light_round_duration

    def create_pyomo_sets(self):
        self.model.rack_Set = Set(initialize=list(range(1, self.rack_num + 1)))
        logging.info("Created self.model.rack_Set: %s" % (len(self.model.rack_Set)))

        self.model.max_lBot_num = ceil(len(self.rack_light_round_duration) / self.lBot_slots_num)
        self.model.lBot_Set = Set(initialize=list(range(1, self.model.max_lBot_num + 1)))
        logging.info("Created self.model.lBot_Set: %s" % len(self.model.lBot_Set))

        self.model.max_wBot_num = ceil(
            sum(len(round_lt) for s, round_lt in self.rack_water_round_duration.items()) / self.wBot_slots_num)
        self.model.wBot_Set = Set(initialize=list(range(1, self.model.max_wBot_num + 1)))
        logging.info("Created self.model.wBot_Set: %s"% len(self.model.wBot_Set))

        self.model.wBot_slot_Set = Set(initialize=list(range(1,  self.wBot_slots_num+1)))
        logging.info("Created self.model.wBot_slot_Set: %s" % len(self.model.wBot_slot_Set))

        self.model.lBot_slot_Set = Set(initialize=list(range(1,  self.lBot_slots_num+1)))
        logging.info("Created self.model.lBot_slot_Set: %s" % len(self.model.lBot_slot_Set))

        self.model.rack_round_water_Set = Set(initialize=[
            (r, v) for r, round_lt in self.rack_water_round_duration.items()
            for v in range(len(round_lt))
        ])
        logging.info("Created self.model.rack_round_water_Set: %s"%(len(self.model.rack_round_water_Set)))

        self.model.rack_round_light_Set = Set(initialize=[
            r for r in self.rack_light_round_duration
        ])
        logging.info("Created self.model.rack_round_light_Set: %s" % (len(self.model.rack_round_light_Set)))

        self.model.wBot_slots = Set(
            initialize=[(b, s) for b in self.model.wBot_Set
            for s in self.model.wBot_slot_Set]
        )
        logging.info("Created self.model.wBot_slots: %s" % len(self.model.wBot_slots))

        self.model.lBot_slots = Set(
            initialize=[(b, s) for b in self.model.lBot_Set
                        for s in self.model.lBot_slot_Set]
        )
        logging.info("Created self.model.lBot_slots: %s" % len(self.model.lBot_slots))
    def build_vars(self):
        self.model.rack_round_wBot_slot_Set = Set(initialize=[
            (r, v, b, s) for (r, v) in self.model.rack_round_water_Set
            for b in self.model.wBot_Set
            for s in self.model.wBot_slot_Set
        ])
        logging.info("Created self.model.rack_round_wBot_slot_Set: %s" % (len(self.model.rack_round_wBot_slot_Set)))

        self.model.whether_rack_round_wBot_slot_var = Var(
            self.model.rack_round_wBot_slot_Set, name='whether_rack_round_wBot_slot_var', domain=Binary
        )
        logging.info("Created self.model.whether_rack_round_wBot_slot_var: %s" % (
            len(self.model.whether_rack_round_wBot_slot_var)))

        self.model.rack_round_lBot_slot_Set = Set(initialize=[
            (r, b, s) for r in self.model.rack_round_light_Set
            for b in self.model.lBot_Set
            for s in self.model.lBot_slot_Set
        ])
        logging.info("Created self.model.rack_round_lBot_slot_Set: %s" % (len(self.model.rack_round_lBot_slot_Set)))

        self.model.whether_rack_round_lBot_slot_var = Var(
            self.model.rack_round_lBot_slot_Set, name='whether_rack_round_lBot_slot_var', domain=Binary
        )
        logging.info("Created self.model.whether_rack_round_lBot_slot_var: %s" % (
            len(self.model.whether_rack_round_lBot_slot_var)))

        self.model.whether_wBot_var = Var(
            self.model.wBot_Set, name='whether_wBot_var', domain=Binary
        )
        logging.info("Created self.model.whether_wBot_var : %s" % (
            len(self.model.whether_wBot_var)))

        self.model.whether_lBot_var = Var(
            self.model.lBot_Set, name='whether_lBot_var', domain=Binary
        )
        logging.info("Created self.model.whether_lBot_var : %s" % (
            len(self.model.whether_lBot_var)))
    def build_whether_robot_constrs(self):

        def whether_wBot_rule(model, b, s):
            return sum(self.model.whether_rack_round_wBot_slot_var[r, v, b, s] * self.rack_water_round_duration[r][v]
                for (r, v) in self.model.rack_round_water_Set) <= self.wBot_slot_length * self.model.whether_wBot_var[b]

        self.model.whether_wBot_contrs = Constraint(self.model.wBot_slots, rule=whether_wBot_rule)
        logging.info("Created  self.model.whether_wBot_contrs: %s"%len( self.model.whether_wBot_contrs ))


        def whether_lBot_rule(model, b, s):
            return sum(self.model.whether_rack_round_lBot_slot_var[r, b, s] * self.rack_light_round_duration[r]
                       for r in self.model.rack_round_light_Set) <= self.lBot_slot_length * \
                self.model.whether_lBot_var[b]

        self.model.whether_lBot_contrs = Constraint(self.model.lBot_slots, rule=whether_lBot_rule)
        logging.info("Created self.model.whether_lBot_contrs: %s" % len(self.model.whether_lBot_contrs))


    def build_one_rack_round_one_bot_slot_constrs(self):
        def one_rack_round_one_wBot_slot_rule(model, r, v):
            return sum(self.model.whether_rack_round_wBot_slot_var[r, v, b, s] for (b, s) in self.model.wBot_slots) == 1

        self.model.one_rack_round_one_wBot_slot_constrs = Constraint(self.model.rack_round_water_Set,
                                                                     rule= one_rack_round_one_wBot_slot_rule)
        logging.info("Created self.model.one_rack_round_one_wBot_slot_constrs: %s" % (
            len(self.model.one_rack_round_one_wBot_slot_constrs)))

        def one_rack_round_one_lBot_slot_rule(model, r):
            return sum(self.model.whether_rack_round_lBot_slot_var[r, b, s] for (b, s) in self.model.lBot_slots) == 1

        self.model.one_rack_round_one_lBot_slot_constrs = Constraint(self.model.rack_round_light_Set,
                                                                     rule=one_rack_round_one_lBot_slot_rule)
        logging.info("Created self.model.one_rack_round_one_lBot_slot_constrs: %s" % (
            len(self.model.one_rack_round_one_lBot_slot_constrs)))

    def solve_minimize_robot_num_obj(self):
        obj = sum(v for k, v in self.model.whether_wBot_var.items()) + sum(
            v for k, v in self.model.whether_lBot_var.items())

        if isinstance(obj, int):
            return True

        try:
            self.model.del_component(self.model.obj)
        except AttributeError:
            pass

        logging.info('start solve_minimize_robot_num_obj')
        self.model.obj = Objective(expr=obj, sense=minimize)
        log_file = self.data_input.output_folder + sp.splitStr + 'solve_minimize_robot_num_obj.log'

        if self.use_api_mode:
            self.opt.set_objective(self.model.obj)
            res = self.opt.solve(self.model, tee=True, logfile=log_file, warmstart=True, options=ROBOT_OBJ_CPLEX_PARAMS)

        else:
            res = self.opt.solve(self.model, tee=True, logfile=log_file, warmstart=True, symbolic_solver_labels=False,
                                 options=ROBOT_OBJ_CPLEX_PARAMS)
        self.log_opt_solve_info(log_file)
        solved = False
        if res.solver.status in [SolverStatus.ok, SolverStatus.aborted]:
            solved = True
            logging.info('finished solve_minimize_robot_num_obj: %s' % value(self.model.obj))
            self.obj_dict['minimize_robot_num_obj'] = value(self.model.obj)

        return solved
    def build_model(self):
        self.create_pyomo_sets()
        self.build_vars()

        self.build_whether_robot_constrs()
        self.build_one_rack_round_one_bot_slot_constrs()

        if self.use_api_mode:
            self.opt.set_instance(self.model)

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