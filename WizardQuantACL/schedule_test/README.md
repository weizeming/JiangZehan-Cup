# ACLScheduleTest

@author: WizardQuant, Advanced Computing Lab 

为了比较方便回测模拟调度算法，让调度算法的研究工作简化。这里尝试将这个部分工作集中在这个项目中。并保证用户使用起来比较方便。

## 下载

* 在本目录下的cmd中执行如下命令

```bash
python setup.py build && python setup.py install 
```

* 或者是直接执行`update.sh` 文件

```bash
./update.sh
```

* 推荐使用python3(3.8+)


## QuickStart

* demo
    * 该样例中，schedule_in_demo和schedule_out_demo是调度平台中原生植入调度算法。（也是未来ACL调度算法研究中，需要自定义的部分。

```py
from ACLScheduleTest.Simulate import Simulator, schedule_in_demo, schedule_out_demo

sim = Simulator()
sim.simulate(schedule_in_demo, schedule_out_demo, mem_bound=35)
```


### 简单解释

* simulate有两个重要参数`schedule_in_func`和`schedule_out_func`
    * 为了使用该平台，目前需要统一这个两个函数输入输出接口。
        * `def schedule_in_demo(workers, cache, av_mem, factor_node_dict, calculated_node_dict, dsk, global_dict):`
            * `workers`: `dict`，调度器中各个workers的状态。
                * `key`: worker名字
                * `value`: worker状态，有两种。`['node', 1]` 表示，`node`节点被worker运行了`1`单位的时间。`None`表示该节点无工作状态
            * `cache`: `dict`，内存存储状态。
                * `key`: `node`名字
                * `value`: 具体数值用于计算。
            * `av_mem`: `float`，当前状态下可用的内存。
            * `factor_node_dict`: `dict`， 因子节点的状态。
                * `key`: `node`名字
                * `value`: 节点输出数值。`None`表示该节点尚未被计算到。
            * `calculated_node_dict`: `dict`，记录是否被计算完的节点。
                * `key`: `node`名字
                * `value`: `bool`
            * `dsk`: `dict`，网络结构。
                * `key`: `node`名字
                * `value`: `(func, args, ...)`，args不定长。
            * `global_dict`: `dict`，用于全局通信的变量，允许自定义。
            * `返回`:返回有两种
                * `None`，表示没办法调用节点
                * `node`，节点名字，表示将该节点被调度起来。
        * `def schedule_out_demo(workers, cache, av_mem, factor_node_dict, calculated_node_dict, dsk, global_dict):`
            * 参数同上面一样。
            * `返回`: 一个list，表示将cache中哪些内容销毁掉，释放内存。
* simulate函数调度流程
    1. 如果没有自定义图，则会默认调用`ACLScheduleTest.data.RandomDsk().build()`生成一个随机的图。（具体参数见`ACLScheduleTest.config`
    2. 如果没有手动指定factorNode，则会默认调用`ACLScheduleTest.utils.get_factor_node()`将dsk中所有出度为0的节点设置为factorNode(并初始化`factor_node_dict`)
    3. 开始调度
        1. 刷新一下状态，每个工作的worker计时器`+1`；把完成任务的节点释放掉。并把结果写进`cache`中
        2. 调用`schedule_out_func`，释放资源
        3. 检查所有worker给没有工作的worker都看看能不能安排好任务（调用`schedule_in_func`）。
    4. 退出调度的条件
        1. 所有`factor_node_dict`都被计算完，此时调度算法正确完成所有任务（`Task Finished`）。
        2. 发现所有worker都休息了，此时调度算法失败（发生阻塞，`Poor Algo`）。
        3. 超出理论最长计算时间，该时间固定为`节点个数 * 完成所有任务的总时间`，此时调度算法失败（`Time limit exceeded`）。
        4. `schedule_in` 尝试计算一个前置资源未准备好的节点，此时调度算法失败（`Look Future`）。
        5. 使用的内存超出内存限制`mem_bound`，调度算法失败（`out_of_mem`）。
	6. 在worker中被调用的节点所需的资源不在cache中


## 关键函数 or 类

* `class ACLScheduleTest.data.RandomDsk`

    * ```py
        def __init__(self, mute=False, node_num=node_num, st_node_num=st_node_num,
                    min_time=min_time, min_time_step=min_time_step, time_lv=time_lv, time_rv=time_rv,
                    mem_peek=mem_peek, mem_pv=mem_pv, mem_sv=mem_sv,
                    link_lv=link_lv, link_rv=link_rv, function_dict=function_dict
                    ):
        ```
        * `mute`:是否打印局部参数log(构造函数仅有参数)
        * `node_num`:图总节点数
        * `st_node_num`:图起点数量(入读为0的节点)
        * `min_time`:每个func最低消耗时间。`time=min_time + randint(time_lv, time_rv) * min_time_step`
        * `mem_peek`:表示整个图最大占用内存大小。`不准确`。只是用来 `avg_mem_peek = mem_peek / node_num * st_node_num`。每个节点的内存计算公式是`avg_mem_peek * (rand() * mem_pv + mem_sv)`
        * `link_lv, link_rv`:用来刻画每个节点可能关联的节点数量。`link_num = randint(link_lv, min(link_rv, node_up_bound))`
        * `function_dict`:`dict`，函数字典。`dict([(link_nun, [function_list])])`，其元素是有多少个输入的函数。

    * `def build(self, **dictParam)`
        * 同样可以输入上面这些参数，但是需要用`param=xxx`的格式。只是局部使用，不改变该对象内部元素。
        * 返回是一个`DAG`（字典）
* `class ACLScheduleTest.Simulate.Simulator`

    * ```py
        def simulate(self, schedule_in_func, schedule_out_func, mem_bound=10, worker_bound=10, dsk=None, factor_node=None,
                plot=True, return_value=False, compare_mode=False, mute=True, **randomDict):
        ```
        * `schedule_in_func, schedule_out_func`:是两个重要函数。需要自定义。

        * `mem_bound`:测试使用内存限制。

        * `worker_bound`:测试使用workers数量。

        * `dsk`: `dict`, 一张图。

        * `factor_node`: `set`, 手动指定节点。

        * `plot`: 是否画图。

        * `return_value`: 是否返回因子计算结果。

        * `compare_mode`: 是否是`compared`模式，该模式下将结果以dict形式返回。
            * 如果成功:
            ```py
            {
                "TaskSuccess": True,
                "schedule_mem_series": schedule_mem_series,
                "schedule_worker_series": schedule_worker_series,
                "bm_mem": bm["mem"],
                "bm_time": bm["time"]
            }
            ```
            * 如果失败:
            ```py
            {
                "TaskSuccess": False
            }
            ```

        * `mute`: 是否打印日志

        * `randomDict`: `param=xxx`格式输入。用于在dsk为空时，传给RandomDsk来build随机调度图。

        * 返回值：在非`compared`模式下：

            * 如果成功，将根据`return_value`参数决定是否返回因子计算结果。
            * 如果失败，将会返回调度失败时刻的`workers, cache, av_mem, factor_node_dict, calculated_node_dict, dsk, global_dict`
    * ```py
        def compare(self, schedule_algo_list, N=10, mem_bound=10, worker_bound=10, dsk=None, factor_node=None, mute=True, analyst=None, rd=None, num_cpus=1, memory_mb=500, **randomDict):
        ```
        * `schedule_algo_list`: `[(algo1_in_func, algo1_out_func), ..., ]`，输入一系列需要对比的策略
        * `N`: 测试次数。
        * `analyst`: `ACLScheduleTest.Analysis.Analyst`实例。见下详解。如果是None，表示返回最原始的输出。`[(simulate(algo) for algo) for test]`
        * `dsk`: 也可以是`[dsk,...] or (dsk,...)`，会进行该参数长度跟N，两者中最小值的测试。
        * `rd`：`RandomDsk`类的实例，用于生成测试用dsk。
        * `num_cpus`：使用多少个cpu核以加速模拟器的调度计算。(默认是1,表示单核计算)
* `class ACLScheduleTest.Analysis.Analyst`

    * ```py
            def run(self, result):
                return success_rate_func(result), speed_up_func(result)
        ```
        * 输入是`class ACLScheduleTest.Simulate.Simulator.simulate(compare_mode=True)`时的返回值列表。
        * 默认调用`ACLScheduleTest.Analysis.success_rate_func`跟`ACLScheduleTest.Analysis.speed_up_func`，可重载。
        * 其中，`ACLScheduleTest.Analysis.success_rate_func` 默认统计调度成功率；`ACLScheduleTest.Analysis.speed_up_func`默认统计调度算法在调度任务上的加速比，返回一个存储所有N次实验加速比的`DataFrame`。
