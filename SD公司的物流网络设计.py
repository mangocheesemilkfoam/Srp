import os
import math
import pandas as pd
import json
import math
from pyomo.environ import *
import pyomo.environ as pyo



class Network(object):

    # __init__函数传入参数：
    # 1、工厂与客户之间的运费
    # 2、工厂与仓库之间的运费
    # 3、仓库与客户之间的运费
    # 4、工厂与客户最低运费
    # 5、仓库与客户最低运费
    # 6、处理费用
    # 7、邮编
    # 8、需求

    def __init__(self, factoryToCustomer, factoryToDc, dcToCustomer, factoryToCustomerMin, dcToCustomerMin, zipcode, demand):

        self.__factoryToCustomer = factoryToCustomer
        self.__factoryToDc = factoryToDc
        self.__dcToCustomer = dcToCustomer
        self.__factoryToCustomerMin = factoryToCustomerMin
        self.__dcToCustomerMin = dcToCustomerMin
        self.__zipcode = zipcode
        self.__demand = demand

        self.__factoryList = list(set([x for x, _ in self.__factoryToCustomer.keys()]))
        self.__dcList = list(set([x for _, x in self.__factoryToCustomer.keys()]))
        self.__customerList = demand.keys()


    def addData(self):
        pass

    def creatModel1(self):

        model = pyo.ConcreteModel(name = "Simplify Model")
        model.ifDc = pyo.Var(self.__dcList, within = pyo.Binary)        # m
        model.ifDcToCustomer = pyo.Var(self.__dcList, self.__customerList, within = pyo.Binary)      # y
        model.cost_factoryTocustomer = pyo.Var(self.__customerList, within = pyo.NonNegativeReals)      # PQ2
        model.cost_dcTocustomer = pyo.Var(self.__dcList, self.__customerList, within = pyo.NonNegativeReals)        # PQ2
        model.time = pyo.Var(self.__dcList, within=pyo.NonNegativeIntegers)     # t

        def obj_rule(md):
            return 40000 / 52 * sum(md.ifDc[i] for i in self.__dcList) + sum(md.cost_factoryTocustomer[j] * (1 - sum(md.ifDcToCustomer[i, j] for i in self.__dcList)) for j in self.__customerList) + \
                   sum(D[i] * P1[i] * md.t[i] / 2 for i in self.__dcList) + sum(
                H[i] * md.ifDcToCustomer[i, j] * N[j] for i in self.__dcList for j in self.__customerList) + sum(md.cost_dcTocustomer[i, j] * md.ifDcToCustomer[i, j] for i in self.__dcList for j in self.__customerList)

        model.obj = pyo.Objective(rule=obj_rule)

        def cross_docking_rule(md, i, j):
            return md.ifDc[i] >= md.ifDcToCustomer[i, j]

        model.cross_docking_rule = pyo.Constraint(self.__dcList, self.__customerList, rule=cross_docking_rule)

        def Factory2DC_rule(md, i):
            return md.t[i] >= sum(md.ifDcToCustomer[i, j] * Q[j] for j in self.__customerList) / 20000

        model.Factory2DC_rule = pyo.Constraint(self.__dcList, rule=Factory2DC_rule)

        def PQ2_rule(md, j):
            return md.cost_factoryTocustomer[j] == max(P2[j] * Q[j], self.__factoryToCustomerMin[j])

        model.PQ2_rule = pyo.Constraint(self.__customerList, rule=PQ2_rule)

        def PQ12_rule(md, i, j):
            return md.cost_dcTocustomer[i, j] == max(P12[i, j] * Q[j], self.__dcToCustomerMin[i, j])

        model.PQ12_rule = pyo.Constraint(self.__dcList, self.__customerList, rule=PQ12_rule)

        def transport_type_rule(md, j):
            return sum(md.ifDcToCustomer[i, j] for i in self.__dcList) <= 1

        model.transport_type_rule = pyo.Constraint(self.__customerList, rule=transport_type_rule)

        return model

    def solve(self, solverName, model):

        self.__solver = pyo.SolverFactory("solverName")
        self.__res = self.__solver.solve(model)
        print(self__res)

    def optimalCost(self):
        pass

    def optimalLocation(self):
        pass

n = Network(P2, P1, P12, )