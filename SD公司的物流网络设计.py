import os
import math
import pandas as pd
import json
import math
from pyomo.environ import *
import pyomo.environ as pyo

class Network(object):

    def __init__(self, fileName):
        self.__USPE_cost = pd.read_excel(fileName, sheet_name = 'USPE运费', index_col = 0)
        self.__USPE_min_cost = pd.read_excel(fileName, sheet_name='USPE最低运价', index_col=0)
        self.__Factory2DC = pd.read_excel(fileName, sheet_name='分拨中心', index_col=0)
        self.__Order_data = pd.read_excel(fileName, sheet_name='订货量', index_col=0)
        self.__Distance_matrix = pd.read_excel(fileName, '全角距离矩阵.xlsx', index_col=0)
        self.__Time_matrix = pd.read_excel(fileName, '全角时间矩阵.xlsx', index_col=0)

        self.__I = list(USPE_cost.columns[1:])
        self.__J = list(USPE_cost.index)
        self.__A = {i: Time_matrix.at['Blawnox', i] for i in I}  # A_{i}工厂到DC_{i}的时间
        self.__B = {(i, j): Time_matrix.at[i, j] for i in I for j in J}  # B_{ij}DC_{i}到分销商j的时间
        self.__C = {j: Time_matrix.at['Blawnox', j] for j in J}
        self.__N = {j: Order_data.at[j, 'Order Number'] for j in J}
        self.__P1 = {i: Factory2DC.at[i, 'Truckload Rate'] for i in I}
        self.__P2 = {j: USPE_cost.at[j, 'Blawnox'] for j in J}
        self.__P12 = {(i, j): USPE_cost.at[j, i] for i in I for j in J}
        self.__Q = {j: Order_data.at[j, 'Weight'] for j in J}
        self.__D = {i: Factory2DC.at[i, 'Distance from Blawnonx'] for i in I}
        self.__H = {i: Factory2DC.at[i, 'Handling Cost'] for i in I}
        self.__LP2 = {j: USPE_min_cost.at[j, 'Blawnox'] for j in J}
        self.__LP12 = {(i, j): USPE_min_cost.at[j, i] for i in I for j in J}

    def creatModel1(self):
        pass

    def optimalCost(self):
        pass

    def optimalLocation(self):
        pass