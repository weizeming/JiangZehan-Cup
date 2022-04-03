# Dashboard

## 代码说明

### Simulator.simulate
```python
from ACLScheduleTest.data import RandomDsk

rd = RandomDsk(
    mute=True, node_num=100,
    st_node_num=10,
    min_time=1, time_lv=0, time_rv=0, min_time_step=0,
    avg_mem_peek=1, mem_pv=0, mem_sv=1
)
sim = Simulator()
sim.simulate(schedule_in_func, schedule_out_func, mem_bound=50, worker_bound=10, rd=rd)
```
rd中的参数是已经给定的，包括
+ 计算节点 node个数 = 100
+ 图起点数量 = 10
+ 计算单位时间 = 1
+ 单位内存 = 1

可以调整的两个参数：
+ mem_bound是内存限制，实际测试中可能更小。
+ worker_bound是可调度的工作器数量。

需要自行完成的两个参数（函数）：
+ schedule_in_func决定分配给每个worker的节点
+ schedule_out_func决定每次计算之后释放的内存

simulate每次调度流程如下：
1. 对已经分配计算节点的worker，执行计算任务；再释放，将自己对应的节点重新设为None
2. 执行一次schedule_out_func, 释放cache中不需要再用到的节点数据
3. 对每个worker(共10个)，依次执行schedule_in_func，决定给这个worker的节点。如果不分配，则返回None

### schedule_in_func

#### 自变量
##### workers
workers是一个dict，表示目前所有workers的工作状态。
+ key: worker的名字，格式化：```worker_{i}```, 示例：```worker_0```。全局所有worker均采取这种格式，
+ value有两种情况
    1. 如果当前worker没有被分配节点任务，则value为```None```
    2. 如果被分配了节点，返回一个长度为2的列表，第1个为即将计算的节点，第2个为0（因为计算时间都是单位1，不需要计算2步)
    示例：```['node_0', 0]```
##### cache
cache是一个dict，表示当前存储的节点数据。因为节点之间有计算的依赖关系，被依赖的节点需要存储已经计算好的数据，这个数据就存储在cache中。
说明：
1. 因为我们只解决调度问题，所以不需要关注cache中具体的数值数据，只关注cache中已经存储了哪些节点的数据。
2. cache中只需要存储被依赖的节点（中间节点）数据，至于最终输出的节点数据（因子节点），会存储在factor_node_dict中，这一部分不占用内存. 
因子节点得到计算结果后会自动存储在factor_node_dict中，因此可以直接释放。
+ key: 节点node的名字，格式化：```node{i}```，示例：```node0```. 全局所有node均采取这种格式。
+ value: 当前节点存储的数值（不关注）

##### av_mem
当前状态下可用内存，格式: float，但在本题中为整数
数值等于 内存限制(mem_bound) - workers内存(已分配节点的worker个数) - cache中数据个数
示例：如果mem_bound=50, 有2个workers被分配了节点，cache中有8条节点数据，则此时mem_bound=40
如果mem_bound=0, 则此时不能分配node给workers

##### factor_node_dict
因子节点的状态，格式：dict
+ key：因子节点的名字，格式化：```node{i}```，示例：```node0```. 全局所有node均采取这种格式。
+ value: 对应节点的计算结果，如果没有被计算到，则为None。示例：如果已被计算，为一数值```3.1415926```（不关注）；如果未被计算，则为```None```

##### calculated_node_dict
所有节点的状态，格式：dict。
+ key为节点名字，格式同上
+ value为bool格式。示例：如果本节点已被计算，则为```True```；如果未被计算，则为```False```

##### dsk
dsk表示本任务中，各节点之间的计算依赖关系。格式：dict
+ key为节点名字，格式同上
+ value：一个元组，长度未定
  + 第一个值为0，是一个lambda函数具体内容不关注
  + 之后为若干个参数。参数可能是数值，也可能是依赖的节点。节点为字符串，格式同上。

value示例1：
```python
(labmda1, 0.1, 0.2)    
```
表示这是一个二元lambda函数，两个自变量为0.1, 0.2。此时不依赖于其他节点，可以直接计算。

value示例2：
```python
(labmda1, 'node1', 'node2')    
```
表示这是一个二元lambda函数，此时依赖于node1和node2两个节点。只有cache中有这两个节点的数据时才可以计算。

Hint：可以利用形如
```python
[arg for arg in dsk[node][1:] if
(arg in nodeList) and (arg not in cache.keys()) and (arg not in workers_nodes)]
```
得到当前```node```还依赖但未被纳入计算范围内的其他节点的列表。

##### global_dict
是一个用于通信的全局变量，用于用户自定义。

#### 返回值
返回一个分配给当前worker的计算节点，格式同上。如果不分配，则返回None

### schedule_out_func
#### 自变量
与schedule_in_func完全相同。

#### 返回值
返回一个list，表示即将被清除出内存的节点。
示例：```['node21', 'node19', 'node71', 'node74']```

### 代码示例
#### 获取未计算的因子节点（集合）
```python
factor_node = set([k for k in factor_node_dict if factor_node_dict[k] is None])
```

#### 获取已分配节点的worker（集合）
```python
workers_nodes = set([workers[k][0] for k in workers if workers[k] is not None])
```

#### 获取所有节点（集合）
```python
nodeList = set(dsk.keys())
```

#### 判断某数据```arg```是否为节点（可能是节点，数值或None）
```python
arg in nodeList
```

#### 判断某节点的计算结果不在cache内存中
```python
arg in nodeList and arg not in cache.keys()
```

#### 获取节点node的依赖节点
```python
[arg for arg in dsk[node][1:] if arg in nodeList ]
```

