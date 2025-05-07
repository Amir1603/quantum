import yaml
import numpy as np


class Conf:
    @staticmethod
    def generate_hk_combinations(conf, step=0.25, max_value=2):
        axis = np.arange(0, max_value + step, step)
        hks = [(h, k) for h in axis for k in axis]

        confs = []
        for h, k in hks:
            new_conf = Conf()
            new_conf.__dict__.update(conf.__dict__)  # Copy existing attributes
            new_conf.h = h
            new_conf.k = k
            confs.append(new_conf)
        return confs

    @staticmethod
    def generate_k_for_h(conf, num_points=50):
        ks = np.linspace(0, 2.0, num_points).tolist()

        confs = []
        for k in ks:
            new_conf = Conf()
            new_conf.__dict__.update(conf.__dict__)  # Copy existing attributes
            new_conf.k = k
            confs.append(new_conf)
        return confs

    @staticmethod
    def generate_p_dephase_values(conf, num_points=1):
        dephases = np.linspace(0, 1.0, num_points).tolist()

        confs = []
        for p in dephases:
            new_conf = Conf()
            new_conf.__dict__.update(conf.__dict__)  # Copy existing attributes
            new_conf.p_dephase = p
            confs.append(new_conf)
        return confs

    @staticmethod
    def generate_backends():
        return ['ibm_kyiv', 'ibm_sherbrooke', 'ibm_brisbane']

    @staticmethod
    def generate_delays():
        return [0]

    @staticmethod
    def generate_thetas(conf, num_points=20):
        thetas = np.linspace(-np.pi, np.pi, num_points).tolist()

        confs = []
        for theta in thetas:
            new_conf = Conf()
            new_conf.__dict__.update(conf.__dict__)  # Copy existing attributes
            new_conf.theta = theta
            confs.append(new_conf)
        return confs

    @staticmethod
    def generate_alice_xor(conf):
        confs = []

        for xor_val in [0, 1]:
            new_conf = Conf()
            new_conf.__dict__.update(conf.__dict__)  # Copy existing attributes
            new_conf.xor_alice_res = xor_val
            confs.append(new_conf)

        return confs

    @staticmethod
    def generate_classical_error(conf, num_points=10):
        probs = np.linspace(0.0, 1.0, num_points).tolist()

        confs = []
        for p in probs:
            new_conf = Conf()
            new_conf.__dict__.update(conf.__dict__)  # Copy existing attributes
            new_conf.p_classical_error = p
            confs.append(new_conf)
        return confs

    @staticmethod
    def generate_depolarization_error(conf, num_points=10):
        probs = np.linspace(0.0, 1.0, num_points).tolist()

        confs = []
        for p in probs:
            new_conf = Conf()
            new_conf.__dict__.update(conf.__dict__)  # Copy existing attributes
            new_conf.p_depol_error = p
            confs.append(new_conf)
        return confs

    @staticmethod
    def generate_bitflip_error(conf, num_points=10):
        probs = np.linspace(0.0, 1.0, num_points).tolist()

        confs = []
        for p in probs:
            new_conf = Conf()
            new_conf.__dict__.update(conf.__dict__)  # Copy existing attributes
            new_conf.p_bitflip_error = p
            confs.append(new_conf)
        return confs

    @staticmethod
    def generate_alice_phase_flip_error(conf, num_points=10):
        probs = np.linspace(0.0, 1.0, num_points).tolist()

        confs = []
        for p in probs:
            new_conf = Conf()
            new_conf.__dict__.update(conf.__dict__)  # Copy existing attributes
            new_conf.p_alice_phaseflip_error = p
            confs.append(new_conf)
        return confs

    @staticmethod
    def generate_bob_phase_flip_error(conf, num_points=10):
        probs = np.linspace(0.0, 1.0, num_points).tolist()

        confs = []
        for p in probs:
            new_conf = Conf()
            new_conf.__dict__.update(conf.__dict__)  # Copy existing attributes
            new_conf.p_bob_phaseflip_error = p
            confs.append(new_conf)
        return confs

    @staticmethod
    def generate_excited_mixture_error(conf, num_points=10):
        probs = np.linspace(0.0, 1.0, num_points).tolist()

        confs = []
        for p in probs:
            new_conf = Conf()
            new_conf.__dict__.update(conf.__dict__)  # Copy existing attributes
            new_conf.p_excited_mixture = p
            confs.append(new_conf)
        return confs

    @staticmethod
    def generate_excited_superposition_error(conf, num_points=10):
        probs = np.linspace(0.0, 1.0, num_points).tolist()

        confs = []
        for p in probs:
            new_conf = Conf()
            new_conf.__dict__.update(conf.__dict__)  # Copy existing attributes
            new_conf.p_excited_superposition_error = p
            confs.append(new_conf)
        return confs

    def __init__(self):
        self.h = 1.0
        self.k = 1.0
        self.total_shots = 10000
        self.error_mitigation = False
        self.run_simulator = True
        self.run_sampler = False
        self.run_all = False
        self.p_dephase = None
        self.backend = None
        self.draw_circuit = False
        self.delay_time = 0
        self.N = 2
        self.theta = None
        self.xor_alice_res = 0
        self.p_classical_error = 0.0
        self.p_depol_error = 0.0
        self.p_bitflip_error = 0.0
        self.p_alice_phaseflip_error = 0.0
        self.p_bob_phaseflip_error = 0.0
        self.p_excited_mixture = 0.0
        self.p_excited_superposition_error = 0.0


    def load(self):
        with open('conf.yaml', 'r') as f:
            self.__dict__ = yaml.load(f, Loader=yaml.FullLoader)    


    def save(self):
        with open('conf.yaml', 'w') as f:
            yaml.dump(self.__dict__, f)


    def __str__(self):
        return str(self.__dict__)


    def __repr__(self):
        return f"<Conf h:{self.h} k:{self.k} total_shots:{self.total_shots} error_mitigation:{self.error_mitigation} run_simulator:{self.run_simulator} run_sampler:{self.run_sampler} run_all:{self.run_all} p_dephase:{self.p_dephase}> <backend:{self.backend}> <draw_circuit:{self.draw_circuit}> <delay_time:{self.delay_time}> <theta:{self.theta}> <N:{self.N}> <xor_alice_res:{self.xor_alice_res}> <p_classical_error:{self.p_classical_error}> <p_depol_error:{self.p_depol_error}> <p_bitflip_error:{self.p_bitflip_error}> <p_alice_phaseflip_error:{self.p_alice_phaseflip_error}> <p_bob_phaseflip_error:{self.p_bob_phaseflip_error}> <p_excited_mixture:{self.p_excited_mixture}> <p_excited_superposition_error:{self.p_excited_superposition_error}>"
