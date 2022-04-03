from ACLScheduleTest.Simulate import Simulator
from ACLScheduleTest.Analysis import Analyst
from ACLScheduleTest.data import RandomDsk
import numpy as np
from time import time

rd = RandomDsk(
    mute=True, node_num=100,
    st_node_num=10,
    min_time=1, time_lv=0, time_rv=0, min_time_step=0,
    avg_mem_peek=1, mem_pv=0, mem_sv=1
)
dsk = rd.build()
sim = Simulator()

num_workers, num_nodes = 10, 100

information = np.ones((num_nodes, num_workers))
def topoOrder(workers, cache, av_mem, factor_node_dict, calculated_node_dict, dsk, global_dict):
    topoQueue = []
    matrix = np.zeros((num_nodes, num_nodes))
    nodeList = list(dsk.keys())
    for idx, node in enumerate(nodeList):
        for n in dsk[node][1:]:
            if n in nodeList:
                id = nodeList.index(n)
                matrix[idx, id] = 1 # idx depends on id
    while len(topoQueue) < len(nodeList):
        for idx, node in enumerate(nodeList):
            if node in topoQueue:
                continue
            if matrix[idx].sum() == 0:
                topoQueue.append(node)
                matrix[:, idx] = 0
    return topoQueue

current_worker_id = 0
iter = 0
from schedule_func_backup import schedule_out_func
def search():
    global current_worker_id, iter
    current_worker_id, iter = 0, 0
    worker_schedules = []
    for idx in range(num_workers):
        worker_schedule = []
        worker_schedules.append(worker_schedule)
    for node_id in range(num_nodes):
        prob = information[node_id] / information[node_id].sum()
        select_worker = np.random.choice(range(num_workers), p=prob)
        worker_schedules[select_worker].append(node_id)
    print(worker_schedules)
    def search_n_func(workers, cache, av_mem, factor_node_dict, calculated_node_dict, dsk, global_dict):
        global current_worker_id, iter
        if len(worker_schedules[current_worker_id])==0:
            return None
        node_id = worker_schedules[current_worker_id][0]
        worker_schedules[current_worker_id].remove(node_id)
        node = f'node{node_id}'
        current_worker_id += 1
        if current_worker_id >= num_workers:
            current_worker_id = 0
            iter += 1
            print(f'iter {iter}')
        #print(current_worker_id)
        nodeList = set(dsk.keys())
        #print(node)
        pre_nodes = [arg for arg in dsk[node][1:] if arg in nodeList]
        for arg in pre_nodes:
            if arg in nodeList and arg not in cache.keys():
                print('None')
                return None
        print(node)
        return node
    result = sim.simulate(search_n_func, schedule_out_func, mem_bound=50, worker_bound=10, rd=rd)
    print(result)

def train(num_epochs, num_agent):
    for epoch in range(num_epochs):
        for agent_idx in range(num_agent):
            search()
