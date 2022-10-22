import os
import math
import pandas as pd
import json
import math
import requests
from pyomo.environ import *
import pyomo.environ as pyo


class Network(object):

    def __init__(self, factoryToCustomer, factoryToDc, dcToCustomer, factoryToCustomerMin, dcToCustomerMin,
                 handling_cost, demand, factoryZipCode, dcZipCode, customerZipCode, order_num, transportMode, apikey):

        '''
        初始化相关参数
        :param factoryToCustomer:工厂与客户之间的运费
        :param factoryToDc:工厂与仓库之间的运费
        :param dcToCustomer:仓库与客户之间的运费
        :param factoryToCustomerMin:工厂与客户最低运费
        :param dcToCustomerMin:仓库与客户最低运费
        :param handling_cost:仓库的包裹处理费用(将企业级的包装换成普通包装所产生的费用)，按照通过仓库的订单数量进行计费
        :param zipcode:地点的邮政编码
        :param demand:客户一周的需求量
        :param order_num:客户一周的订单数量(对应包裹数量计算处理成本)
        :param distance:两点之间的距离(工厂到仓库、工厂到客户、仓库到客户) ————暂时使用（可用API根据邮政编码获取经纬度后进行计算）!!!
        :param time:两点间采用货车运输所需时间(工厂到仓库、工厂到客户、仓库到客户) ————暂时使用（可用API根据邮政编码获取经纬度后进行计算）!!!
        '''
        self.__factoryToCustomer = factoryToCustomer
        self.__factoryToDc = factoryToDc
        self.__dcToCustomer = dcToCustomer
        self.__factoryToCustomerMin = factoryToCustomerMin
        self.__dcToCustomerMin = dcToCustomerMin
        self.__handling_cost = handling_cost

        self.__factoryZipCode = factoryZipCode
        self.__dcZipCode = dcZipCode
        self.__customerZipCode = customerZipCode
        self.__cityZipCode = {}
        self.__cityZipCode.update(self.__factoryZipCode)
        self.__cityZipCode.update(self.__dcZipCode)
        self.__cityZipCode.update(self.__customerZipCode)

        self.__demand = demand
        self.__order_num = order_num

        self.__factoryList = list(set([x for x, _ in self.__factoryToCustomer.keys()]))
        self.__dcList = list(set([x for _, x in self.__factoryToDc.keys()]))
        self.__customerList = list(self.__demand.keys())
        self.__cityList = self.__factoryList + self.__dcList + self.__customerList

        self.__distance = self.get_transport_info(transportMode, apikey)[0]
        self.__time = self.get_transport_info(transportMode, apikey)[1]

    def get_coordinate(self, city, zipCode, apikey):

        '''
        :param city: 城市名
        :param zipCode: 城市的邮编
        :param apikey: 你的apikey
        :return: 该城市的经纬度
        '''
        base_url = 'https://api.geoapify.com/v1/geocode/search'  # 官方给出的API查询接口

        request_parameters = {
            'apiKey': apikey,  # 这里填自己获取的API密钥
            'postcode': zipCode,  # 这里填地址的邮政编码
            'text': city,  # 这里填地址
            'format': 'json'  # 返回json类型格式的数据
        }

        res = requests.get(base_url, params=request_parameters)
        return [res.json()['results'][0]['lon'], res.json()['results'][0]['lat']]

    def get_transport_info(self, transportMode, apikey):

        '''
        :param transportMode: 运输工具（卡车，铁路等）
        :param apikey: 你的apikey
        :return: 返回距离和时间
        '''
        distance = {}
        time = {}
        source = {}
        sourceList = []
        for city in self.__cityList:
            source['location'] = self.get_coordinate(city, self.__cityZipCode[city], apikey)
            sourceList.append(source)

        baseUrl = "https://api.geoapify.com/v1/routematrix?apiKey=" + apikey

        for i in range(len(self.__cityList) - 1):
            start = self.__cityList[i]
            data = {
                "mode": transportMode,
                "sources": [sourceList[i]],
                "targets": sourceList
            }
            res = requests.post(url=baseUrl, json=data).json()['sources_to_targets']

            for j in range(i + 1, len(self.__cityList)):
                end = self.__cityList[j]
                distance[(start, end)] = res[0][j]['distance']
                time[(start, end)] = res[0][j]['time']

        return distance, time

    def add_model(self):
        model = pyo.ConcreteModel(name="Network Optimization Model")

        model.ifDc = pyo.Var(self.__dcList, within=pyo.Binary)  # 是否建立转运中心
        model.ifDcToCustomer = pyo.Var(self.__dcList, self.__customerList, within=pyo.Binary)  # 是否从转运中心发往客户
        model.cost_factoryTocustomer = pyo.Var(self.__factoryList, self.__customerList,
                                               within=pyo.NonNegativeReals)  # 客户从工厂发货的费用（直运方式）
        model.cost_dcTocustomer = pyo.Var(self.__dcList, self.__customerList,
                                          within=pyo.NonNegativeReals)  # 客户从仓库发货的费用（转运方式后半程）
        model.truckload_num = pyo.Var(self.__factoryList, self.__dcList,
                                      within=pyo.NonNegativeIntegers)  # 从工厂到某个仓库的整车运输次数

        # Create Objective Function
        # 最小化运输总成本的目标函数
        def cost_obj(md):
            return sum(
                self.__factoryToDc[f, d] * self.__distance[f, d] * md.truckload_num[f, d] for f in self.__factoryList
                for d in self.__dcList) + \
                   sum(md.ifDcToCustomer[d, c] * md.cost_dcTocustomer[d, c] for d in self.__dcList for c in
                       self.__customerList) + \
                   sum((1 - sum(md.ifDcToCustomer[d, c] for d in self.__dcList)) * md.cost_factoryTocustomer[f, c] for f
                       in self.__factoryList
                       for c in self.__customerList) + \
                   sum(self.__handling_cost[d] * md.ifDcToCustomer[d, c] * self.__order_num[c] for d in self.__dcList
                       for c in self.__customerList) + \
                   40000 / 52 * sum(md.ifDc[d] for d in self.__dcList)

        model.cost_obj = pyo.Objective(rule=cost_obj)

        # 货物运输重量的目标函数（避免与USPE间的合约运输违约风险，多目标优化可以采用该目标函数）
        def freight_weight_obj(md):
            return sum(self.__demand[c] * md.ifDcToCustomer[d, c] for d in self.__dcList for c in self.__customerList)

        # 最小化运输总时间的目标函数（优化客户的运输体验，多目标优化可以采用该目标函数）
        def transportation_time_obj(md):
            return sum(md.ifDc[d] * self.__time[f, d] * md.truckload_num[f, d] for f in self.__factoryList for d in
                       self.__dcList) + \
                   sum(md.ifDcToCustomer[d, c] * self.__time[d, c] * self.__order_num[c] for d in self.__dcList for c in
                       self.__customerList) + \
                   sum((1 - sum(md.ifDcToCustomer[d, c] for d in self.__dcList for c in self.__customerList)) *
                       self.__time[f, c] * self.__order_num[c] for
                       f in self.__factoryList for c in self.__customerList) + \
                   sum(302400 * self.__order_num[c] * md.ifDcToCustomer[d, c] for d in self.__dcList for c in
                       self.__customerList)

        # Create Constraints Rules
        def depot_flow_rule(md, d, c):
            return md.ifDc[d] >= md.ifDcToCustomer[d, c]

        model.depot_flow_rule = pyo.Constraint(self.__dcList, self.__customerList, rule=depot_flow_rule)

        def transportation_type_rule(md, c):
            return sum(md.ifDcToCustomer[d, c] for d in self.__dcList) <= 1

        model.transportation_type_rule = pyo.Constraint(self.__customerList, rule=transportation_type_rule)

        def f2d_vehicle_num_rule(md, f, d):
            return sum(md.ifDcToCustomer[d, c] * self.__demand[c] for c in self.__customerList) / 20000 == \
                   md.truckload_num[f, d]

        model.f2d_vehicle_num_rule = pyo.Constraint(self.__factoryList, self.__dcList, rule=f2d_vehicle_num_rule)

        def qualify_cost_dc_rule(md, d, c):
            return md.cost_dcTocustomer[d, c] == max(self.__dcToCustomer[d, c] * self.__demand[c],
                                                     self.__dcToCustomerMin[d, c])

        model.qualify_cost_dc_rule = pyo.Constraint(self.__dcList, self.__customerList, rule=qualify_cost_dc_rule)

        def qualify_cost_fc_rule(md, f, c):
            return md.cost_factoryTocustomer[f, c] == max(self.__factoryToCustomer[f, c] * self.__demand[c],
                                                          self.__factoryToCustomerMin[f, c])

        model.qualify_cost_fc_rule = pyo.Constraint(self.__factoryList, self.__customerList, rule=qualify_cost_fc_rule)

        return model

    def solve_model(self, solverName):
        opt = pyo.SolverFactory(solverName, solver_io="python")
        self.__model = self.add_model()
        self.__solution = opt.solve(self.__model)


    def export_data(self):
        self.__model.display()
        self.__model.pprint()

# 测试代码
test_data_path = './test/data/data.xlsx'

# 读取excel数据源的所有数据
data_Indices = pd.read_excel(test_data_path,sheet_name='Indices')
data_zipcode = pd.read_excel(test_data_path, sheet_name='Zipcode', index_col = 0)
data_Cost_matrix = pd.read_excel(test_data_path,sheet_name='Cost',index_col=0)
data_Handling_Cost = pd.read_excel(test_data_path,sheet_name='Handling Cost',index_col=0)
data_Minimum_Cost_matrix = pd.read_excel(test_data_path,sheet_name='Minimum Cost',index_col=0)
data_Time_matrix = pd.read_excel(test_data_path,sheet_name='Time',index_col=0)
data_Distance_matrix = pd.read_excel(test_data_path,sheet_name='Distance',index_col=0)
data_Customer_Information = pd.read_excel(test_data_path,sheet_name='Customer Information',index_col=0)
# 读取预先计算好的参数数据
data_contract_Qualify_Cost = pd.read_excel(test_data_path,sheet_name='Qualify Cost',index_col=0)  # 合约费率
data_public_Qualify_Cost = pd.read_excel(test_data_path,sheet_name='Public Qualify Cost',index_col=0)  # 非合约费率

# 提取相关索引
raw_Factories = [i for i in data_Indices['Factories'].values.tolist() if str(i)!='nan']
raw_Depots = [i for i in data_Indices['Depots'].values.tolist() if str(i)!='nan']
raw_Customers = [i for i in data_Indices['Customers'].values.tolist() if str(i)!='nan']
raw_Cities = raw_Factories + raw_Depots + raw_Customers


# 测试参数的初始化
factoryToCustomer = {(factory, customer): data_Cost_matrix.at[factory, customer] for factory in raw_Factories for customer in raw_Customers}  # 工厂到顾客的运费
factoryToDc = {(factory, depot): data_Cost_matrix.at[factory, depot] for factory in raw_Factories for depot in raw_Depots}  # 工厂到仓库的运费
dcToCustomer = {(depot, customer): data_Cost_matrix.at[depot, customer] for depot in raw_Depots for customer in raw_Customers}  # 仓库到顾客的运费
factoryToCustomerMin = {(factory, customer): data_Minimum_Cost_matrix.at[factory, customer] for factory in raw_Factories for customer in raw_Customers}  # 工厂到顾客的最低运费
dcToCustomerMin = {(depot, customer): data_Minimum_Cost_matrix.at[depot, customer] for depot in raw_Depots for customer in raw_Customers}  # 仓库到顾客的最低运费
handling_cost = {depot: data_Handling_Cost.at[depot, 'Handling Cost'] for depot in raw_Depots}  # 仓库的装卸费

factoryZipCode = {factory: data_zipcode.at[factory, 'Zipcode'] for factory in raw_Factories}
dcZipCode = {depot: data_zipcode.at[depot, 'Zipcode'] for depot in raw_Depots}
customerZipCode = {customer: data_zipcode.at[customer, 'Zipcode'] for customer in raw_Customers}

demand = {customer: data_Customer_Information.at[customer, 'Demand'] for customer in raw_Customers}  # 顾客的需求量
order_num = {customer: data_Customer_Information.at[customer, 'Order'] for customer in raw_Customers}  # 顾客的订单量
distance = {(source,destination):data_Distance_matrix.at[source,destination] for source in raw_Cities for destination in raw_Cities if str(data_Distance_matrix.at[source,destination]) != 'nan'}
time = {(source,destination):data_Time_matrix.at[source,destination] for source in raw_Cities for destination in raw_Cities if str(data_Time_matrix.at[source,destination]) != 'nan'}
transportMode = 'truck'
apikey = '05d2f10de78e400e90d1ddf1ee2fa91f'

a = Network(factoryToCustomer, factoryToDc, dcToCustomer,factoryToCustomerMin, dcToCustomerMin, handling_cost, demand, factoryZipCode, dcZipCode, customerZipCode, order_num, transportMode, apikey)
a.add_model()
a.solve_model('gurobi')
a.export_data()