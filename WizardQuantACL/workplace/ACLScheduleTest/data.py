try:
    from .basic import Func
    from .config import *
except Exception as e:
    from basic import Func
    from config import *

import random


class RandomDsk(object):
    def __init__(self, mute=False, node_num=node_num, st_node_num=st_node_num,
                 min_time=min_time, min_time_step=min_time_step, time_lv=time_lv, time_rv=time_rv,
                 mem_peek=mem_peek, mem_pv=mem_pv, mem_sv=mem_sv, avg_mem_peek=None,
                 link_lv=link_lv, link_rv=link_rv, function_dict=function_dict
                 ):

        self.globalParam = dict(
            node_num=node_num,
            st_node_num=st_node_num,
            min_time=min_time,
            min_time_step=min_time_step,
            time_lv=time_lv,
            time_rv=time_rv,
            mem_peek=mem_peek,
            mem_pv=mem_pv,
            mem_sv=mem_sv,
            avg_mem_peek=avg_mem_peek,
            link_lv=link_lv,
            link_rv=link_rv,
            function_dict=function_dict
        )
        self.mute = mute

    def build(self, **dictParam):
        localParam = self.globalParam.copy()
        localParam.update(dictParam)

        localParam["link_lv"] = max(localParam["link_lv"], min(localParam["function_dict"].keys()))
        localParam["link_rv"] = min(localParam["link_rv"], max(localParam["function_dict"].keys()))
        if not self.mute:
            print("localParam", localParam)

        for int_key in ["st_node_num", "node_num"]:
            localParam[int_key] = int(localParam[int_key])
        assert localParam["st_node_num"] <= localParam["node_num"]
        if localParam["avg_mem_peek"] is None:
            localParam["avg_mem_peek"] = (localParam["mem_peek"] / localParam["node_num"]) * localParam["st_node_num"]

        dsk = {}

        def random_f(input_value=False, node_up_bound=None, ):
            time_consume = localParam["min_time"] + localParam["min_time_step"] * random.randint(
                localParam["time_lv"], localParam["time_rv"]
            )
            mem_consume = localParam["avg_mem_peek"] * (random.random() * localParam["mem_pv"] + localParam["mem_sv"])
            link_num = random.randint(localParam['link_lv'],
                                      min(localParam['link_rv'], node_up_bound) if node_up_bound else localParam[
                                          'link_rv'])

            func_index = random.randint(0, len(localParam["function_dict"][link_num]) - 1)
            func = localParam["function_dict"][link_num][func_index]

            if input_value:
                return time_consume, mem_consume, link_num, func, [random.random() for i in range(link_num)]
            return time_consume, mem_consume, link_num, func

        for st_i in range(localParam["st_node_num"]):
            time_consume, mem_consume, link_num, func, inputList = random_f(input_value=True)
            dsk["node" + str(st_i)] = (Func(time=time_consume, mem=mem_consume, func=func), *inputList)

        for node_i in range(localParam["st_node_num"], localParam["node_num"]):
            time_consume, mem_consume, link_num, func = random_f(input_value=False, node_up_bound=len(dsk.keys()))

            links_nodes = random.sample(list(dsk.keys()), link_num)

            mem_used = sum(map(lambda l_x: dsk[l_x][0].mem, links_nodes))
            mem_consume = min(mem_consume, localParam["mem_peek"] - mem_used)

            dsk["node" + str(node_i)] = (Func(time=time_consume, mem=mem_consume, func=func), *links_nodes)
        return dsk


if __name__ == '__main__':
    rd = RandomDsk()

    print(rd.build(st_node_num=2))
