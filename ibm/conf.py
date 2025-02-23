import os
import yaml


class Conf:
    def __init__(self):
        if 'conf.yaml' in os.listdir():
            self.load()
        else:
            self.h = 1.0
            self.k = 1.0
            self.total_shots = 1024
            self.error_mitigation = False
            self.run_simulator = True
            self.run_sampler = True
            self.run_estimator = True
            self.run_all = False
            self.p_dephase_list = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
            self.backends = []


    def load(self):
        with open('conf.yaml', 'r') as f:
            self.__dict__ = yaml.load(f, Loader=yaml.FullLoader)    


    def save(self):
        with open('conf.yaml', 'w') as f:
            yaml.dump(self.__dict__, f)


    def __str__(self):
        return str(self.__dict__)


    def __repr__(self):
        return f"<Conf h:{self.h} v:{self.v} total_shots:{self.total_shots} error_mitigation:{self.error_mitigation} run_simulator:{self.run_simulator} run_sampler:{self.run_sampler} run_estimator:{self.run_estimator} run_all:{self.run_all} p_dephase_list:{self.p_dephase_list}>"
