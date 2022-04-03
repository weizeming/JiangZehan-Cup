from ACLScheduleTest.Simulate import Simulator
from ACLScheduleTest.Analysis import Analyst
from ACLScheduleTest.data import RandomDsk
import numpy as np
from time import time


from schedule_func_backup import schedule_out_func

rd = RandomDsk(
    mute=True, node_num=100,
    st_node_num=10,
    min_time=1, time_lv=0, time_rv=0, min_time_step=0,
    avg_mem_peek=1, mem_pv=0, mem_sv=1
)
dsk = rd.build()
sim = Simulator()

demo_trace = []
worker_id = 0
def schedule_in_demo_trace(workers, cache, av_mem, factor_node_dict, calculated_node_dict, dsk, global_dict):
    global worker_id, demo_trace
    ori_id = worker_id
    worker_id += 1
    if worker_id >= 10:
        worker_id = 0
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
    demo_trace.append([ori_id, int(available_node()[4:])])
    return available_node()

sim.simulate(schedule_in_demo_trace, schedule_out_func, mem_bound=50, worker_bound=10,dsk=dsk,rd=rd, compare_mode=True)

print(demo_trace)

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

import math
def reward(x):
    t = 0.001
    baseline = 6
    alpha = 0.3
    return max(x - baseline, 0) * t

current_worker_id = 0
iter = 0
def search(dsk):
    global current_worker_id, iter
    current_worker_id, iter = 0, 0
    worker_schedules = []
    worker_traces = np.zeros((num_nodes, num_workers))
    for idx in range(num_workers):
        worker_schedule = []
        worker_schedules.append(worker_schedule)
    for node_id in range(num_nodes):
        prob = information[node_id] / information[node_id].sum()
        select_worker = np.random.choice(range(num_workers), p=prob)
        worker_schedules[select_worker].append(node_id)
        worker_traces[node_id, select_worker] = 1
    #print(worker_schedules)
    def search_n_func(workers, cache, av_mem, factor_node_dict, calculated_node_dict, dsk, global_dict):
        global current_worker_id, iter
        ori_id = current_worker_id

        current_worker_id += 1
        if current_worker_id >= num_workers:
            current_worker_id = 0
            iter += 1
            #print(f'\niter {iter}')
        #print(current_worker_id)
        if av_mem == 0:
            return None
        if len(worker_schedules[ori_id])==0:
            return None
        node_id = worker_schedules[ori_id][0]
        node = f'node{node_id}'
        nodeList = set(dsk.keys())
        #print(node)

        pre_nodes = [arg for arg in dsk[node][1:] if arg in nodeList]
        #print(pre_nodes)
        for arg in pre_nodes:
            if arg in nodeList and arg not in cache.keys():
                #print('None\n', '-'*100)
                return None
        worker_schedules[ori_id].remove(node_id)
        #print(node, '\n', '-'*100)
        return node

    result = sim.simulate(search_n_func, schedule_out_func, mem_bound=50, worker_bound=10,dsk=dsk,rd=rd, compare_mode=True)
    analyst = Analyst()
    success_rate, speed_up = analyst.run(result=[[result]])
    speed_up = speed_up.values.item()
    success_rate = success_rate[0]
    rewarded = np.array([reward(speed_up)]) * success_rate
    return speed_up, success_rate,  rewarded * worker_traces

rd = RandomDsk(mute=True)
def train(num_epochs, num_agent, alpha):
    global  information
    for epoch in range(num_epochs):
        start_time = time()
        new_information = np.zeros((num_nodes, num_workers))
        speed_up_total = 0
        success_total = 0
        for agent_idx in range(num_agent):
            speed_up, success_rate, rewarded = search(dsk)
            new_information += rewarded
            speed_up_total += speed_up
            success_total += success_rate
        information = alpha * information + new_information
        print(f'epoch {epoch+1}: speed_up = {speed_up_total / num_agent:.3f}, success_rate = {success_total/num_agent} Use time: {time()-start_time:.1f}')
        #print(information)
train(20, 100, 1)