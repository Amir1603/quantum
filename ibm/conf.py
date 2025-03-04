import yaml


class Conf:
    def generate_all_confs():
        parameters = [(1, 0.2), (1, 0.5), (1, 1), (1.5, 1)] # (h, k) list
        p_dephase_list = [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        backends = []#'ibm_kyiv', 'ibm_sherbrooke', 'ibm_brisbane']
        delays = [0]

        confs = []

        for p in parameters:
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
