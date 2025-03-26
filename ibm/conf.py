import yaml
import numpy as np


class Conf:
    def generate_all_confs():
        #parameters = [(1, 0.2), (1, 0.5), (1, 1), (1.5, 1)] # (h, k) list
        step = 0.25
        axis = np.arange(0, 2 + step, step)  # Include 2 by adding step to the stop value
        parameters = [(h, k) for h in axis for k in axis]  # Generate all (h, k) combinations
        p_dephase_list = [0] #[0, 0.25, 0.5, 0.75, 1.0]
        backends = []#'ibm_kyiv', 'ibm_sherbrooke', 'ibm_brisbane']
        delays = [0]
        thetas = [np.pi]#np.linspace(-np.pi, np.pi, 50)

        confs = []

        for p in parameters:
            for theta in thetas:
                for delay in delays:
                    for p_dephase in p_dephase_list:
                        conf = Conf()
                        conf.h = p[0]
                        conf.k = p[1]
                        conf.total_shots = 10000
                        conf.error_mitigation = False
                        conf.run_simulator = True
                        conf.run_sampler = False
                        conf.run_estimator = False
                        conf.run_all = False
                        conf.p_dephase = p_dephase
                        conf.backend = None
                        conf.draw_circuit = True
                        conf.delay_time = delay
                        conf.theta = theta

                        confs.append(conf)

                    for backend in backends:
                        conf = Conf()
                        conf.h = p[0]
                        conf.k = p[1]
                        conf.total_shots = 10000
                        conf.error_mitigation = False
                        conf.run_simulator = True
                        conf.run_sampler = True
                        conf.run_estimator = False
                        conf.run_all = False
                        conf.p_dephase = None
                        conf.backend = backend
                        conf.draw_circuit = False
                        conf.delay_time = delay
                        conf.theta = theta

                        confs.append(conf)

        return confs

    def __init__(self):
        self.h = 1.0
        self.k = 1.0
        self.total_shots = 1024
        self.error_mitigation = False
        self.run_simulator = True
        self.run_sampler = True
        self.run_estimator = True
        self.run_all = False
        self.p_dephase = None
        self.backend = None
        self.draw_circuit = False
        self.delay_time = 10000
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
        return f"<Conf h:{self.h} k:{self.k} total_shots:{self.total_shots} error_mitigation:{self.error_mitigation} run_simulator:{self.run_simulator} run_sampler:{self.run_sampler} run_estimator:{self.run_estimator} run_all:{self.run_all} p_dephase:{self.p_dephase}> <backend:{self.backend}> <draw_circuit:{self.draw_circuit}> <delay_time:{self.delay_time}>"
