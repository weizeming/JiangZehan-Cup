from ACLScheduleTest.Simulate import Simulator
from ACLScheduleTest.Analysis import Analyst
from ACLScheduleTest.data import RandomDsk

from schedule_func import schedule_in_func, schedule_out_func

rd = RandomDsk(
    mute=True, node_num=100,
    st_node_num=10,
    min_time=1, time_lv=0, time_rv=0, min_time_step=0,
    avg_mem_peek=1, mem_pv=0, mem_sv=1
)

sim = Simulator()

analyst = Analyst()

result = sim.simulate(schedule_in_func, schedule_out_func, mem_bound=50, worker_bound=10, rd=rd)
print(result)

sucess_rate, speed_up = sim.compare([(schedule_in_func, schedule_out_func),], rd=rd, mem_bound=50, analyst=analyst, num_cpus=3, N=100)
print(sucess_rate, speed_up)