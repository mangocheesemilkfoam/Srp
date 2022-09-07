# 优化模型建立

## 1. 模型假设

1. 从工厂发往转运仓库的订单为**整车运输**(按运输次数和距离计算运输成本和运输时间)；从工厂/转运仓库发往客户的订单为**零担运输**(按订单数计算运输成本和运输时间)
2. 假设每周的需求没有波动，且相关按年计算的费用能平摊到每周上面



## 2. 模型符号说明

---

### 2.1 符号标识

$ f \in \text{Factories} = \{\text{Blawnox}\} $
$ d \in Depots = \{\text{City of Industry},\text{Coos Bay},\text{Laughlin},\text{Preston},\text{Tuba City},\text{Vacaville},\text{Walla Walla}\} $ (共7个)
$ c \in \text{Customers} = \{\text{Columbus},\text{Clancy},\cdots,\text{Spokane},\text{Prosser}\} $ (共43个)

$ \text{Cities} = \text{Factories} \cup \text{Depots} \cup \text{Customers} $

(其中$f$为工厂的集合,$d$为转运仓库的集合,$c$为分销商/顾客的集合)



### 2.2 参数

$ \text{cost}_{s,t} \in \mathbb{R}^{+}:\text{从起点s到终点t的运输费率} $ 
$ \text{handling cost}_{d} \in \mathbb{R}^{+}:\text{转运仓库d对单个订单包裹的处理费用} $ 
$ \text{minimum cost}_{s,t} \in \mathbb{R}^{+}:\text{从起点s到终点t的最低运输费用} $ 
$ \text{distance}_{s,t} \in \mathbb{R}^{+}:\text{从起点s到终点t的运输距离(公路距离)} $ 
$ \text{time}_{s,t} \in \mathbb{R}^{+}:\text{从起点s到终点t的运输时间(卡车所需的时间)} $ 
$ \text{demand}_{c} \in \mathbb{R}^{+}:\text{分销商/客户c的订货量(每周)} $ 
$ \text{order}_{c} \in \mathbb{R}^{+}:\text{分销商/客户c的订单数量(每周)} $ 
$ \text{transportnum}_{s,t} \in \mathbb{N}^{+} :\text{从起点s到转运仓库d所需的整车运输次数} $

$ \text{qualify cost}_{d,c} : \text{将所订货物从转运仓库d运输到分销商/顾客c所需的费用(预先根据订货量计算)}$ 

$ \text{qualify cost}_{f,c} : \text{将所订货物从工厂f运输到分销商/顾客c所需的费用(预先根据订货量计算)}$ 



`运输费率补充说明`

- $cost_{s,t}$数据类型说明

| 费率类型               | 起点        | 终点        | 费率单位      | 是否有最低运费? |
| ---------------------- | ----------- | ----------- | ------------- | --------------- |
| `DJ Rates`(Shared)     | `Factories` | `Depots`    | `$ per Mile`  | `—`             |
| `USPE Proposed Rates`  | `Factories` | `Customers` | `$ per Pound` | `Yes`           |
| `USPE Published Rates` | `Depots`    | `Customers` | `$ per Pound` | `Yes`           |



### 2.3 决策变量

---

$\text{open depot}_{d} \in [0,1]$: 是否租用转运仓库$d$？

$\text{transport type}_{d,c} \in [0,1]$: 分销商/客户$c$使用直接配送(用$0$表示)还是采用仓库$d$越库配送(用$1$表示)



### 2.4 目标函数

---

在这个问题中，共涉及到三种利益相关方：SD公司、USPE公司、分销商/客户。每一方都有各自的利益侧重点，而它们的目标往往是相互矛盾的，因此在建模过程中我们采用两种思路：首先单独考虑使得SD公司利益最大化(也就是降低总运输成本)的方案；然后结合三个利益相关方采用目标规划(Goal Programming)的建模思路，按照每个利益方的目标优先顺序逐步优化(Hierarchy Approach)以达到全局的最优化，考虑到案例所描述的“采用转运网络增加的延迟在可接受范围内”，因此这三个目标的优先级顺序确定为：SD公司>USPE公司>分销商/客户

各个利益相关方的目标如下目标函数所示：

- **SD公司：实现成本最小化**: 通过优化不同分销商/客户的运输策略以及建立对应的转运仓库来降低总运输成本，运输成本构成如下：

  1. 直接运输成本：从工厂到仓库，从仓库到客户，从工厂到客户
  2. 转运仓库的包裹处理费用：因为在转运仓库中需要将SD公司与USPE按合约费用计费的包裹的包装拆开，换成公共的普通包装以USPE的公共费率进行运输，因此需要对每个订单(shipment)收取一定的处理费用
  3. 转运仓库的租金

  $$
  % 从工厂到转运仓库的运输费用(与另一家公司共用卡车，费用平摊)
  \text{Minimize} \quad \text{Total Cost} = 
  \sum_{(f,d) \in \text{Factories} \times \text{Depots}} \frac{\text{cost}_{f,d}*distance_{f,d}*transportnum_{f,d}}{2} + \\
  
  % 从转运仓库到客户的运输费用
  \sum_{(d,c) \in \text{Depots} \times \text{Customers}}
  \text{transport type}_{d,c}*\text{qualify cost}_{d,c} + \\
  
  % 直接从工厂发往客户的运输费用
  \sum_{(f,c) \in \text{Factories} \times \text{Customers}} 
  (1-\sum_{d \in \text{Depots}} \text{transport type}_{d,c})*\text{qualify cost}_{f,c} + \\
  
  % 转运中心的包裹处理费用(一个shipment对应一个订单)
  \sum_{(d,c) \in \text{Depots} \times \text{Customers}} \text{handling cost}_{d}*\text{transport type}_{d,c}*order_{c} + \\
  
  % 平摊到每周的仓库租金
  \frac{40000}{52} \sum_{d \in \text{Depots}} \text{open depot}_{d}
  $$



- **USPE公司：运输货物的重量**: 从题目中了解到，在USPE运输能力能够满足SD公司需求的时候，SD公司不能寻找第三方物流企业合作。由于SD公司通过USPE运输的货物重量直接影响到USPE的利润，因此如果SD公司通过USPE合约费用运输的货物重量急剧下降，则USPE可能会怀疑SD公司的行为，存在一定的违约风险。因此在这个目标中将优化SD公司通过USPE合约运输的货物重量。如下是该目标的表达式：
  $$
  \text{Maximize} \quad \text{Freight Weight} = \sum_{c \in \text{Customers}} demand_{c}*(1-\sum_{d \in \text{Depots}}\text{transport type}_{d,c})
  $$


​	

- **分销商/客户：提高响应性，降低货物的在途时间**: 通过转运仓库虽然对于某些客户而言能够节省一定的成本，但是在转运仓库中进行的拆包和重新包装需要一定的时间，而且部分的分销商/客户通过转运方式运输的总距离可能比直接运输的总距离更远，这样在一定程度上延迟了响应时间。虽然这个影响比较小，但是在我们的多目标优化模型中予以考虑。运输时间主要有以下两部分组成：
1. 路途中的运输时间：从工厂到仓库、从仓库到分销商/客户、从工厂到分销商/客户
  
2. 转运仓库中的包裹处理时间：对于时间的确定，我们假设分销商/客户采购的多批订单集中配送，工厂每周汇总每个分销商/客户的订单，统一进行发货，因此在转运仓库$d$的包裹处理时间可以近似取：$302400s$

$$
\text{Minimize} \quad \text{Transportation Time} =
% 工厂到转运仓库的运输时间((\text{open depot}_{d})为潜在的冗余变量)
\sum_{(f,d) \in \text{Factories} \times \text{Depots}}
\text{time}_{f,d}*\text{transportnum}_{f,d} + \\

% 转运仓库到客户的运输时间
\sum_{(d,c) \in \text{Depots} \times \text{Customers}} 
\text{transport type}_{d,c}*\text{time}_{d,c}*\text{order}_{c} + \\

% 工厂到客户的直接运输时间
\sum_{(f,c) \in \text{Factories} \times \text{Customers}}
(1-\sum_{d \in \text{Depots}}\text{transport type}_{d,c})*\text{time}_{f,c}*order_{c} + \\

% 订单的处理时间
\sum_{(d,c) \in \text{Depots} \times \text{Customers}} \text{handling time}_{d}*order_{c}*\text{transport type}_{d,c}
$$



### 2.5 约束条件

---

- **转运仓库的转运约束**: 需要建立转运仓库$d$后分销商/客户才能通过转运仓库$d$进行交叉转运
  $$
  \text{open depot}_{d} \geq \text{transport type}_{d,c} \quad \forall d \in \text{Depots}, \forall c \in \text{Cutomers}
  $$

- **分销商/客户运输方式约束**: 每个分销商/客户只能采用**1**种转运仓库
  $$
  \sum_{d \in \text{Depots}}\text{transport type}_{d,c} \le 1 \quad \forall c \in \text{Customers}
  $$

- **工厂到转运仓库的运输次数约束**: 计算模型的`transnum`参数
  $$
  \text{transportnum}_{f,d} = \lceil {\frac{\sum_{c\in \text{Customers}}\text{transport type}_{d,c}*demand_{c}}{20000}} \rceil \quad f \in \text{Blawnox},\forall d \in \text{Depots}
  $$
  
- **最低运费约束**: 每种运输方式(从工厂到转运仓库除外,因为采用与另一家企业共同采用整车运输)的运价需要超过最低起运价格，如果低于起运价则按起运价收费
  $$
  \text{qualify cost}_{d,c} = max\{cost_{d,c}*demand_{c}, \text{minimum cost}_{d,c}\} \\
  \text{qualify cost}_{f,c} = max\{cost_{f,c}*demand_{c}, \text{minimum cost}_{d,c}\}
  $$
  

### 2.6 可选的约束—用于其他方案的比较评估

- **启用的仓库数量**: 限定最多启用的转运仓库数量

$$
\sum_{d \in \text{Depots}}open_{d} \le 2
$$



## 3. 数据的采集及模型的代码实现

### 3.1 地理位置坐标的编码 (Address Geocoding)

为了将不同区域间的距离量化以计算从工厂到分销仓库的成本；将时间量化以优化路途中的运输时间提高响应性，进而提高分销商/客户的满意度，需要将原始数据的地址进行编码，换算成经纬度方便后续的运算。在这里我们采用**Geoapify**的API服务，传入每个地区的邮政编码(ZIP Code)和城市名称以获取经纬度数据。示例数据如下：

| 城市名称 | 邮政编码 | 经度     | 纬度     |
| -------- | -------- | -------- | -------- |
| Columbus | 59019    | -83.0007 | 39.96226 |
| Clancy   | 59634    | -111.986 | 46.46485 |
| ...      | ...      | ...      | ...      |

接着将不同城市的坐标两两匹配，调用**Geoapify**的路径规划API获取距离和卡车整车运输的预估时间，分别构成$51\times51$的距离矩阵与时间矩阵



### 3.2 数据的整理

为了便于批量导入模型进行计算，预先将原始数据转换为矩阵类型的数据，并设置好相应的索引方面模型的读取，共整理出5个工作簿



### 3.3 模型的代码实现

由于Gurobi Solver支持MultiObjectives的多目标优化且求解性能较强，因此我们采用Gurobi封装的API进行建模及模型求解，建模及求解步骤如下图所示：

![img](https://tva1.sinaimg.cn/large/008i3skNgy1gqck0l7mr1j313505p756.jpg)

#### 3.3.1 变量的定义示例

```python
# 模型初始化及决策变量的添加
model = gp.Model('Transportaion Network Problem')
transportnum = model.addVars(Factories,Depots,vtype=GRB.INTEGER,name='transportnum_{f,d}')
open_depot = model.addVars(Depots,vtype=GRB.BINARY,name='opened_depot_{d}')
transport_type = model.addVars(Depots,Customers,vtype=GRB.BINARY,name='transport type_{d,c}')
```

#### 3.3.2 目标函数的定义示例

```python
# 创建最小化运输成本的目标函数
cost_obj = model.setObjective(
    gp.quicksum(cost[f,d] * distance[f,d] * transportnum[f,d] * 0.000621371192 / 2 for f in Factories for d in Depots) + gp.quicksum(transport_type[d,c] * qualify_cost_dc[d,c] for d in Depots for c in Customers) + gp.quicksum((1-gp.quicksum(transport_type[d,c] for d in Depots)) * qualify_cost_fc[f,c] for f in Factories for c in Customers) + gp.quicksum(handling_cost[d] * transport_type[d,c] * order[c] for d in Depots for c in Customers) + 40000/52 * gp.quicksum(open_depot[d] for d in Depots),GRB.MINIMIZE
)
```

#### 3.3.3 约束条件的定义示例

```python
# 转运仓库约束：有仓库才能进行转运
depot_flow_rule = model.addConstrs(open_depot[d] >= transport_type[d,c] for d in Depots for c in Customers)

# 运输类型约束：一个客户只能使用一种运输方式(直送或者转运配送)
transportation_type_rule = model.addConstrs(gp.quicksum(transport_type[d,c] for d in Depots) <= 1 for c in Customers)

# 工厂到仓库的运输车辆约束
f2d_vehicle_rule = model.addConstrs(transportnum[f,d] >= gp.quicksum(transport_type[d,c]*demand[c] for c in Customers) / 20000 for f in Factories for d in Depots)
```



## 4. 结果分析

### 4.1 单目标优化—最小化SD公司的运输成本

通过求解可知最优成本为：**17079.624926262626**，相关决策参数如下：

| 建立的仓库名称 | 从工厂到该仓库的运输次数 |
| -------------- | ------------------------ |
| Tuba City      | 1                        |
| Walla Walla    | 1                        |

使用转运的情况

| 转运仓库    | 服务的分销商/客户                                            | 数量 |
| :---------- | ------------------------------------------------------------ | ---- |
| Tuba City   | Buellton, Cortez, Delta, Flagstaff, Fort Mohave, Fresno, Grand Junction, Las Vegas, Los Angeles, Moab, Oxnard, Phoeniz, Polacca, Prescott Valley, Rifle, Salinas, Santa Clara, Washington | 18   |
| Walla Walla | American Fork, Aurora, Boise, Brewster, Carlin, Clancy, Columbus, Eagle Point, Ferndale, Fernley, Jerome, McCall, Milton Freewater, Missoula, Ogden, Orofino, Prosser, Reno, Renton, San Mateo, Spokane, Susanville, Westfall, Wilson, Yuba City | 25   |

可见在只考虑成本而不考虑其他因素的情况下，全部分销商/客户采用转运的方式能够使得总成本最低，此时通过USPE公司运输的货物量为0，在一定程度上损害了USPE利益，存在较强的毁约可能性，因此下面我们考虑综合三个目标的优化。



### 4.2 多目标优化—权衡各个利益相关方的利益

在求解的过程中，采用了**Hierarchical/lexicographic**的方法构建目标函数，设置目标索引和优先级，以及reltol(relative tolerance)

```python
# 建立SD公司的成本优化目标
multi_cost_obj = model.setObjectiveN(
    gp.quicksum(cost[f,d] * distance[f,d] * transportnum[f,d] / 2 for f in Factories for d in Depots) + gp.quicksum(transport_type[d,c] * cost[d,c] * demand[c] for d in Depots for c in Customers) + gp.quicksum((1-gp.quicksum(transport_type[d,c] for d in Depots)) * cost[f,c] * demand[c] for f in Factories for c in Customers) + gp.quicksum(handling_cost[d] * transport_type[d,c] * order[c] for d in Depots for c in Customers) + 40000/52 * gp.quicksum(open_depot[d] for d in Depots),
    index=0,
    priority=5
)

# 建立USPE公司的货物运量优化目标
multi_freight_weight_obj = model.setObjectiveN(
    gp.quicksum(demand[c]*transport_type[d,c] for d in Depots for c in Customers),
    index=1,
    priority=3
)

# 建立分销商/客户的运输
multi_transport_time_obj = model.setObjectiveN(
     gp.quicksum(time[f,d] * transportnum[f,d] for f in Factories for d in Depots) + gp.quicksum(transport_type[d,c] * time[d,c] * order[c] for d in Depots for c in Customers) + gp.quicksum((1-gp.quicksum(transport_type[d,c] for d in Depots)) * time[f,c] * order[c] for f in Factories for c in Customers) + gp.quicksum(302400 * order[c] * transport_type[d,c] for d in Depots for c in Customers),
    index=2,
    priority=1
)
```

通过求解可知最优成本为：**20265.162799999995**，从相关决策参数可知，在这种情况下没有建立新仓库，对于所有分销商/客户采取直接配送的方法，可能的原因是该方案在SD公司节省的成本的重要程度没有与维持USPE的合作关系以及保持优质的响应性和客户服务重要
