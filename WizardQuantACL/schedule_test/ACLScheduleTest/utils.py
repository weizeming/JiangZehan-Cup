def get_factor_node(dsk):
    factor_node = set(dsk.keys())
    nodeList = dsk.keys()
    for node in nodeList:
        factor_node -= set(dsk[node][1:])
    return factor_node


def get_start_node(dsk):
    start_node = []
    nodeList = dsk.keys()
    for node in nodeList:
        isStartNode = True
        for arg in dsk[node][1:]:
            if arg in nodeList:
                isStartNode = False
                break
        if isStartNode:
            start_node.append(node)
    return start_node


def poor_dsk_check(dsk, mem_bound):
    for node in dsk.keys():
        mem_used = dsk[node][0].mem + sum(map(lambda l_x: dsk[l_x][0].mem if l_x in dsk else 0, dsk[node][1:]))
        if mem_used > mem_bound:
            return True
    return False


def get_reverse_dsk(dsk):
    nodeList = dsk.keys()
    dskT = {node: [] for node in nodeList}
    for node in nodeList:
        args = dsk[node][1:]
        for a_n in filter(lambda x: x in nodeList, args):
            dskT[a_n].append(node)
    return dskT


def my_max(alist):
    if len(alist):
        return max(alist)
    return 0


def bm_consume(dsk):
    bm = {
        'mem': 0,
        'time': 0
    }
    for node in dsk.keys():
        bm['mem'] += dsk[node][0].mem
        bm['time'] += dsk[node][0].time
    return bm


def get_max_time_consume(dsk):
    return sum(val[0].time for val in dsk.values()) * len(dsk.keys())
