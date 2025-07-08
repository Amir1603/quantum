import yaml
import numpy as np


class ErrorsConf:
    @staticmethod
    def generate_classical_error(num_points=21):
        probs = np.linspace(0.0, 1.0, num_points).tolist()

        confs = []
        for p in probs:
            new_conf = ErrorsConf()
            new_conf.p_classical_error = p
            confs.append(new_conf)
        return confs

    @staticmethod
    def generate_depolarization_error(num_points=21):
        probs = np.linspace(0.0, 1.0, num_points).tolist()

        confs = []
        for p in probs:
            new_conf = ErrorsConf()
            new_conf.p_depol_error = p
            confs.append(new_conf)
        return confs

    @staticmethod
    def generate_bitflip_error(num_points=11):
        probs = np.linspace(0.0, 0.5, num_points).tolist()

        confs = []
        for p in probs:
            new_conf = ErrorsConf()
            new_conf.p_bitflip_error = p
            confs.append(new_conf)
        return confs

    @staticmethod
    def generate_alice_phase_flip_error(num_points=21):
        probs = np.linspace(0.0, 1.0, num_points).tolist()

        confs = []
        for p in probs:
            new_conf = ErrorsConf()
            new_conf.p_alice_phaseflip_error = p
            confs.append(new_conf)
        return confs

    @staticmethod
    def generate_bob_phase_flip_error(num_points=21):
        probs = np.linspace(0.0, 1.0, num_points).tolist()

        confs = []
        for p in probs:
            new_conf = ErrorsConf()
            new_conf.p_bob_phaseflip_error = p
            confs.append(new_conf)
        return confs

    @staticmethod
    def generate_excited_mixture_error(num_points=21):
        probs = np.linspace(0.0, 1.0, num_points).tolist()

        confs = []
        for p in probs:
            new_conf = ErrorsConf()
            new_conf.p_excited_mixture_error = p
            confs.append(new_conf)
        return confs

    @staticmethod
    def generate_excited_superposition_error(num_points=21):
        probs = np.linspace(0.0, 1.0, num_points).tolist()

        confs = []
        for p in probs:
            new_conf = ErrorsConf()
            new_conf.p_excited_superposition_error = p
            confs.append(new_conf)
        return confs

    def __init__(self):
        self.p_classical_error = 0.0
        self.p_depol_error = 0.0
        self.p_bitflip_error = 0.0
        self.p_alice_phaseflip_error = 0.0
        self.p_bob_phaseflip_error = 0.0
        self.p_excited_mixture_error = 0.0
        self.p_excited_superposition_error = 0.0


class Conf:
    @staticmethod
    def generate_hJ_combinations(conf, step=0.25, max_value=2):
        axis = np.arange(0, max_value + step, step)
        hJs = [(h, J) for h in axis for J in axis]

        confs = []
        for h, J in hJs:
            new_conf = Conf(conf.N)
            new_conf.__dict__.update(conf.__dict__)  # Copy existing attributes
            new_conf.h = h
            new_conf.J = J
            confs.append(new_conf)
        return confs

    @staticmethod
    def generate_J_for_h(conf, num_points=40, avoid_0=False):
        max_J = 4.0
        min_J = max_J/num_points if avoid_0 else 0.0
        Js = np.linspace(min_J, max_J, num_points).tolist()

        confs = []
        for J in Js:
            new_conf = Conf(conf.N)
            new_conf.__dict__.update(conf.__dict__)  # Copy existing attributes
            new_conf.J = J
            confs.append(new_conf)
        return confs

    @staticmethod
    def generate_alice_xor(conf):
        confs = []

        for xor_val in [0, 1]:
            new_conf = QuantumSimConf(conf.N)
            new_conf.__dict__.update(conf.__dict__)  # Copy existing attributes
            new_conf.xor_alice_res = xor_val
            confs.append(new_conf)

        return confs

    @staticmethod
    def generate_from_errors(conf, errors_list: list[ErrorsConf]):
        confs = []

        for errors in errors_list:
            new_conf = QuantumSimConf(conf.N)
            new_conf.__dict__.update(conf.__dict__)  # Copy existing attributes
            new_conf.errors = errors
            confs.append(new_conf)

        return confs

    def __init__(self, N: int):
        self.N = N

        self.h = 1.0
        self.J = 1.0
        self.xor_alice_res = 0
        self.errors = ErrorsConf()


class QuantumSimConf(Conf):
    @staticmethod
    def generate_p_dephase_values(conf, num_points=1):
        dephases = np.linspace(0, 1.0, num_points).tolist()

        confs = []
        for p in dephases:
            new_conf = QuantumSimConf(conf.N)
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

    def __init__(self, N):
        super().__init__(N)

        self.total_shots = 10000
        self.error_mitigation = False
        self.run_simulator = True
        self.run_sampler = False
        self.run_all = False
        self.p_dephase = None
        self.backend = None
        self.draw_circuit = False
        self.delay_time = 0

    def __str__(self):
        return str(self.__dict__)
