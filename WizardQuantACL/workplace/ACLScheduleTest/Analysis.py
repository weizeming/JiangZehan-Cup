import pandas as pd


class Analyst(object):
    def __init__(self):
        pass

    def run(self, result):
        return success_rate_func(result), speed_up_func(result)


def success_rate_func(result):
    algo_success_time = []
    for test in result:
        algo_len = len(test)
        if len(algo_success_time) == 0:
            algo_success_time = [0 for _ in range(algo_len)]
        for i in range(algo_len):
            algo_success_time[i] += test[i]["TaskSuccess"]
    N = len(result)
    return list(map(lambda x: x / N, algo_success_time))


def speed_up_func(result):
    speed_up_rate = []
    for test in result:
        if all([algo['TaskSuccess'] for algo in test]):
            speed_up_rate.append([algo["bm_time"] / len(algo["schedule_mem_series"]) for algo in test])
    return pd.DataFrame(speed_up_rate)
