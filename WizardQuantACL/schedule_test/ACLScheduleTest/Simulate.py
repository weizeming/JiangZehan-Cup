import matplotlib.pyplot as plt
import pandas as pd
import contextlib
import copy
# import ray

try:
    from .basic import Func
    from .data import RandomDsk
    from .config import *
    from .utils import get_factor_node, poor_dsk_check, bm_consume, get_max_time_consume
    from .Analysis import Analyst
except Exception as e:
    from basic import Func
    from data import RandomDsk
    from config import *
    from utils import get_factor_node, poor_dsk_check, bm_consume, get_max_time_consume
    from Analysis import Analyst


class Simulator(object):
    def __init__(self):
        pass

    @staticmethod
    def gen_time_index(max_time, min_time_step):
        Bound = (max_time + min_time_step)
        time_index = []
        i = 0
        while (i - 1) * min_time_step <= Bound:
            time_index.append(i * min_time_step)
            i += 1
        return time_index

    @staticmethod
    def gen_mem_values(dsk, scheduleTable, time_index):
        values = []
        for ti in time_index:
            mem_value = 0
            for node in scheduleTable:
                if scheduleTable[node][0] <= ti <= scheduleTable[node][1]:
                    mem_value += dsk[node][0].mem
            values.append(mem_value)
        return pd.Series(values, index=time_index)

    @staticmethod
    def simulate(schedule_in_func, schedule_out_func, mem_bound=10, worker_bound=10, dsk=None, factor_node=None,
                 plot=True, return_value=False, compare_mode=False, mute=True, rd=None, **randomDict):

        assert callable(schedule_in_func) and callable(schedule_out_func)
        if dsk is None:
            if rd is None:
                rd = RandomDsk(mute=mute)
                dsk = rd.build(**randomDict)
            else:
                if mute:
                    rd.mute = mute
                dsk = rd.build()

        if poor_dsk_check(dsk, mem_bound):
            if not mute:
                print("[FAIL][Poor dsk]")
            return None

        workers = {
            "worker_%d" % i: None for i in range(worker_bound)
        }
        cache = {}
        if factor_node is None:
            factor_node = get_factor_node(dsk)  # self-defined is also ok
        elif callable(factor_node):
            factor_node = factor_node(dsk)
        factor_node_dict = {
            node: None for node in factor_node
        }
        calculated_node_dict = {
            node: False for node in dsk.keys()
        }
        av_mem = mem_bound
        mem_series = []
        worker_series = []
        TaskSuccess = False

        @contextlib.contextmanager  # added by hgr
        def save_context():
            nonlocal workers, cache, factor_node_dict, calculated_node_dict, dsk
            ctx_local = copy.deepcopy(locals())

            yield None

            workers, cache, factor_node_dict, calculated_node_dict, dsk = ctx_local['workers'],                 \
                                                                          ctx_local['cache'],                   \
                                                                          ctx_local['factor_node_dict'],        \
                                                                          ctx_local['calculated_node_dict'],    \
                                                                          ctx_local['dsk']

        global_dict = {}
        nodeList = dsk.keys()
        look_future_check = False
        out_of_mem = False
        time_consume = 0
        time_limit = get_max_time_consume(dsk)
        while True:
            # update
            for w in workers:
                if workers[w] is not None:
                    workers[w][1] += 1
                    node = workers[w][0]
                    if dsk[node][0].time <= workers[w][1]:
                        # update cache
                        nodeFunc = dsk[node][0]
                        nodeArgs = dsk[node][1:]

                        nodeArgs = list(map(lambda x: cache[x] if x in cache else x, nodeArgs))

                        value = nodeFunc(*nodeArgs)
                        cache[node] = value

                        # update factor_node_dict
                        if node in factor_node_dict:
                            factor_node_dict[node] = value

                        calculated_node_dict[node] = True

                        # update workers
                        workers[w] = None

            # release trash
            with save_context():  # added by hgr
                out_cache_list = schedule_out_func(workers, cache, av_mem, factor_node_dict, calculated_node_dict, dsk,
                                                   global_dict)
            cache = {k: cache[k] for k in cache if k not in out_cache_list}
            av_mem += sum([dsk[node][0].mem for node in out_cache_list])


            wn_check = True
            for w in workers:
                if workers[w] is not None:
                    wn_args = dsk[workers[w][0]][1:]
                    wn_args = list(filter(lambda x: x in dsk.keys(), wn_args))
                    if (len(wn_args) > 0) and (not all(map(lambda x: x in cache, wn_args))):
                        wn_check = False
                        break 

            if not wn_check:
                if not mute:
                    print(f"[FAIL][Poor Algo] Poor Swept. Some Args in need are not in cache now.")
                break

            # schedule it
            working_workers = 0
            for w in workers:
                if workers[w] is None:
                    with save_context():  # added by hgr
                        av_node = schedule_in_func(workers, cache, av_mem, factor_node_dict, calculated_node_dict, dsk,
                                                   global_dict)

                    if av_node is not None:
                        if all(map(lambda t_x: (t_x not in nodeList) or (t_x in cache), dsk[av_node][1:])):
                            if av_mem < dsk[av_node][0].mem:
                                out_of_mem = True
                                break
                            workers[w] = [av_node, 0]
                            av_mem -= dsk[av_node][0].mem
                        else:
                            look_future_check = True
                            break
                if workers[w]:
                    working_workers += 1
            mem_used = mem_bound - av_mem
            mem_series.append(mem_used)
            worker_series.append(working_workers)

            # update timer
            time_consume += 1
            if time_consume >= time_limit:
                if not mute:
                    print(f"[FAIL][Poor Algo] time limit <{time_limit}> exceeded.")
                break

            if look_future_check:
                if not mute:
                    print("[FAIL][Poor Algo] look future. Some Args in need are not in cache now.")
                break

            if out_of_mem:
                if not mute:
                    print("[FAIL][Poor Algo] out_of_mem.")
                break

            if all([factor_node_dict[fn] is not None for fn in factor_node_dict]):
                if not mute:
                    print("[SUCCESS]Task Finished")
                TaskSuccess = True
                break

            if all([workers[w] is None for w in workers]):
                if not mute:
                    print("[FAIL][Poor Algo] cache_mem/mem_bound:%.5f" % (
                            sum([dsk[c_n][0].mem for c_n in cache.keys()]) / mem_bound))
                break

        if compare_mode:
            if TaskSuccess:
                schedule_mem_series = pd.Series(mem_series)
                schedule_worker_series = pd.Series(worker_series)

                bm = bm_consume(dsk)

                return {
                    "TaskSuccess": True,
                    "schedule_mem_series": schedule_mem_series,
                    "schedule_worker_series": schedule_worker_series,
                    "bm_mem": bm["mem"],
                    "bm_time": bm["time"]
                }
            else:
                return {
                    "TaskSuccess": False
                }

        if TaskSuccess:
            schedule_mem_series = pd.Series(mem_series)
            schedule_worker_series = pd.Series(worker_series)
            print("=========summary info============")
            print("Time:", len(mem_series))
            print("Mem Peek:", max(mem_series))
            print("MemUsingRate:", sum(mem_series) / len(mem_series) / mem_bound)
            print("WorkerUsingRate:", sum(worker_series) / len(mem_series) / worker_bound)

            if plot:
                schedule_mem_series.plot()
                plt.show()
                schedule_worker_series.plot()
                plt.show()
            if return_value:
                return factor_node_dict
        else:
            return workers, cache, av_mem, factor_node_dict, calculated_node_dict, dsk, global_dict

    
    @staticmethod
    def simulate_ray(schedule_in_func, schedule_out_func, mem_bound=10, worker_bound=10, dsk=None, factor_node=None,
                    plot=True, return_value=False, compare_mode=False, mute=True, rd=None, **randomDict):
        return Simulator.simulate(schedule_in_func, 
                                schedule_out_func, 
                                mem_bound=mem_bound, 
                                worker_bound=worker_bound, 
                                dsk=dsk,
                                factor_node=factor_node, 
                                compare_mode=True)

    @staticmethod
    def compare(schedule_algo_list, N=10, mem_bound=10, worker_bound=10, dsk=None, factor_node=None, mute=True,
                analyst=None, rd=None, num_cpus=1, memory_mb=500, **randomDict):
        if isinstance(dsk, (tuple, list)):
            dsk_list = list(dsk[:N])
        elif isinstance(dsk, dict):
            dsk_list = [dsk, ]
        elif rd is None:
            rd = RandomDsk(mute=mute)
            dsk_list = [rd.build(**randomDict) for _ in range(N)]
        else:
            dsk_list = [rd.build() for _ in range(N)]
        
        result = []
        if num_cpus >= 1:
            for dsk in dsk_list:
                local_result = []
                for algo in schedule_algo_list:
                    algo_result = Simulator.simulate(algo[0], algo[1], mem_bound=mem_bound, worker_bound=worker_bound, dsk=dsk,
                                                factor_node=factor_node, compare_mode=True)
                    local_result.append(algo_result)
                result.append(local_result)
        elif num_cpus >= 2:
            @contextlib.contextmanager 
            def ray_init_context(num_cpus, memory_mb=500):
                if not ray.is_initialized():
                    ray.init(num_cpus=num_cpus, _memory=num_cpus * memory_mb * 1024 * 1024)
                yield 

                if ray.is_initialized():
                    ray.shutdown()
            with ray_init_context(num_cpus=num_cpus, memory_mb=memory_mb):
                algo_len = len(schedule_algo_list)
                result_ray = [Simulator.simulate_ray.remote(algo[0], algo[1], mem_bound=mem_bound, worker_bound=worker_bound, dsk=dsk,
                                                    factor_node=factor_node, compare_mode=True) for dsk in dsk_list for algo in schedule_algo_list]
                result_ray = ray.get(result_ray)

                result = [result_ray[i:i+algo_len] for i in range(0, len(result_ray), algo_len)]

        if analyst is None:
            return result
        else:
            return analyst.run(result)

def schedule_in_demo(workers, cache, av_mem, factor_node_dict, calculated_node_dict, dsk, global_dict):
    # need to calculater
    factor_node = set([k for k in factor_node_dict if factor_node_dict[k] is None])

    if len(factor_node) == 0:
        return None

    workers_nodes = set([workers[k][0] for k in workers if workers[k] is not None])

    def topoOrder():
        topoQueue = []
        q = list(factor_node - set(cache.keys()) - workers_nodes)

        nodeList = set(dsk.keys()) - set(factor_node)
        while len(q):
            node, q = q[0], q[1:]

            topoQueue.append(node)

            append_nodes = [arg for arg in dsk[node][1:] if
                            (arg in nodeList) and (arg not in cache.keys()) and (arg not in workers_nodes)]
            nodeList = nodeList - set(append_nodes)
            q = q + append_nodes
        return topoQueue

    topo_node = topoOrder()

    nodeList = dsk.keys()

    def available_node():
        for node in topo_node:
            if dsk[node][0].mem > av_mem:
                continue
            args = dsk[node][1:]
            isAvailable = True
            for arg in args:
                if (arg in nodeList) and (arg not in cache):
                    isAvailable = False
                    break
            if isAvailable:
                return node
        return None

    return available_node()


def schedule_out_demo(workers, cache, av_mem, factor_node_dict, calculated_node_dict, dsk, global_dict):
    # need to calculater
    factor_node = set([k for k in factor_node_dict if factor_node_dict[k] is None])

    if len(factor_node) == 0:
        return []

    workers_nodes = set([workers[k][0] for k in workers if workers[k] is not None])

    def topoOrder():
        topoQueue = []
        q = list(factor_node - set(cache.keys()) - workers_nodes)

        nodeList = set(dsk.keys()) - set(factor_node)
        while len(q):
            node, q = q[0], q[1:]

            topoQueue.append(node)

            append_nodes = [arg for arg in dsk[node][1:] if
                            (arg in nodeList) and (arg not in cache.keys()) and (arg not in workers_nodes)]
            nodeList = nodeList - set(append_nodes)
            q = q + append_nodes
        return topoQueue

    topo_node = topoOrder()

    def trash_cache():
        trash_node = []

        for node in cache:
            isTrash = True
            for tp_node in topo_node + list(workers_nodes):
                if node in dsk[tp_node][1:]:
                    isTrash = False
                    break
            if isTrash:
                trash_node.append(node)
        return trash_node

    return trash_cache()


if __name__ == '__main__':
    sim = Simulator()
    sim.simulate(schedule_in_demo, schedule_out_demo, mem_bound=30)
    analyst = Analyst()
    success_rate, speed_up = sim.compare([(schedule_in_demo, schedule_out_demo),
                                          (schedule_in_demo, schedule_out_demo)],
                                         mem_bound=30, node_num=1000,
                                         analyst=analyst, 
                                         num_cpus=10
                                         )
    print(success_rate)
    if len(speed_up) > 0:
        speed_up.plot()
        plt.show()
