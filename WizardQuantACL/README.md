# 项目文档

@author: WizardQuant, Advanced Computing Lab 
@email-contact: `huzeyu@wizardquant.com`

推荐使用环境：`Linux+Python3.8+` 

1. 已经写好了便于回测调度算法的平台`ACLScheduleTest`, 在`schedule_test`目录根据该目录下的`README.md`文件进行安装。基于`ACLScheduleTest`，写了名为`demo`的notebook，用于参考。
2. WizardQuant提供了额外的计算资源，以及搭建好了对应的回测环境，通过ssh连接`101.201.80.221`，账号密码已经发给学校，由学校提供。有任何比赛相关问题or需求可以联系`huzeyu@wizardquant.com`。
3. 另外也提供了一套script版本的测试方案。修改`schedule_func.py`的`schedule_in_func`和`schedule_out_func`这两个函数即可。运行通过`python main.py`即可得到对应结果，也可以通过修改`demo[notebook]` or `main.py` 完成自定义测试。此外，**在回测平台中保留的`schedule_func.py`的文件，有利于最终各个队伍之间的算法性能进行比较**，因此最好完成本地测试。

