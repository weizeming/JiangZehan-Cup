import numpy as np

node_num = 100
st_node_num = 10
min_time = 1
min_time_step = 1
time_lv = 1
time_rv = 10
mem_peek = 10
mem_pv = 0.6
mem_sv = 0.5
link_lv = 1
link_rv = 3

function_dict = {
    1: [
        lambda x: np.sqrt(max(x, 0.1)),
        lambda x: (1. / x) if x != 0 else 0,
        lambda x: x + 1
    ],
    2: [
        lambda x, y: x + y,
        lambda x, y: x - y,
        lambda x, y: x * y,
        lambda x, y: (x / y) if y != 0 else x,
    ],
    3: [
        lambda x, y, z: x + y + z,
        lambda x, y, z: x * y + z,
        lambda x, y, z: x + y - z,
        lambda x, y, z: (x + y / z) if z != 0 else (x + y),
    ]
}
