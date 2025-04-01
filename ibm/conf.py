import yaml
import numpy as np


class Conf:
    @staticmethod
    def generate_hk_combinations(conf, step=0.25, max_value=2):
        axis = np.arange(0, max_value + step, step)
        hks = [(h, k) for h in axis for k in axis]

        return [Conf(h=h, k=k, **conf.__dict__) for h, k in hks]

    @staticmethod
    def generate_k_for_h(conf, step=0.25, max_value=2):
        axis = np.arange(0, max_value + step, step)
        hks =[(conf.h, k) for k in axis]

        return [Conf(h=h, k=k, **conf.__dict__) for h, k in hks]

    @staticmethod
    def generate_p_dephase_values(conf, num_points=1):
        dephases = np.linspace(0, 1.0, num_points).tolist()

        return [Conf(p_dephase=p, **conf.__dict__) for p in dephases]

    @staticmethod
    def generate_backends():
        return ['ibm_kyiv', 'ibm_sherbrooke', 'ibm_brisbane']

    @staticmethod
    def generate_delays():
        return [0]

    @staticmethod
    def generate_thetas(conf, num_points=50):
        thetas = np.linspace(-np.pi, np.pi, num_points).tolist()

        return [Conf(theta=theta, **conf.__dict__) for theta in thetas]

    def __init__(self):
        self.h = 1.0
        self.k = 1.0
        self.total_shots = 10000
        self.error_mitigation = False
        self.run_simulator = True
        self.run_sampler = True
        self.run_estimator = False
        self.run_all = False
        self.p_dephase = None
        self.backend = None
        self.draw_circuit = False
        self.delay_time = 0
        self.n_qubits = 2
        self.theta = np.pi


    def load(self):
        with open('conf.yaml', 'r') as f:
            self.__dict__ = yaml.load(f, Loader=yaml.FullLoader)    


    def save(self):
        with open('conf.yaml', 'w') as f:
            yaml.dump(self.__dict__, f)


    def __str__(self):
        return str(self.__dict__)


    def __repr__(self):
        return f"<Conf h:{self.h} k:{self.k} total_shots:{self.total_shots} error_mitigation:{self.error_mitigation} run_simulator:{self.run_simulator} run_sampler:{self.run_sampler} run_estimator:{self.run_estimator} run_all:{self.run_all} p_dephase:{self.p_dephase}> <backend:{self.backend}> <draw_circuit:{self.draw_circuit}> <delay_time:{self.delay_time}> <theta:{self.theta}> <n_qubits:{self.n_qubits}>"
