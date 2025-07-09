from utils import AliceBase
from Calculators import Operators
from conf import ErrorsConf


class NumericalRunConf:
    @staticmethod
    def AliceConf():
        return NumericalRunConf(
            'alice',
            Operators.alice_H,
            [Operators.alice_HB, Operators.QB],
            [AliceBase.X],
            [1, 2, 3, 4]
        )

    @staticmethod
    def NNConf():
        return NumericalRunConf(
            'nn',
            Operators.nn_H,
            [Operators.nn_HB, Operators.QB],
            [AliceBase.X, AliceBase.Y],
            [2, 3, 4]
        )

    @staticmethod
    def get_ylim(error_name: str, OB_type: str):
        if OB_type == 'alice_HB':
            if error_name == 'p_bitflip_error': return (-0.1, 0.5)
            if error_name == 'p_alice_phaseflip_error': return (-0.1, 0.5)
            if error_name == 'p_bob_phaseflip_error': return (-0.1, 0.5)
            if error_name == 'p_excited_mixture_error': return (-0.1, 0.2)
            if error_name == 'p_excited_superposition_error': return (-0.1, 0.2)
        elif OB_type == 'nn_HB':
            if error_name == 'p_bitflip_error': return (-0.1, 0.5)
            if error_name == 'p_bob_phaseflip_error': return (-0.1, 0.5)

        return None

    @staticmethod
    def generate_errors_configurations(error_name: str):
        if error_name == 'p_classical_error': return ErrorsConf.generate_classical_error()
        if error_name == 'p_depol_error': return ErrorsConf.generate_depolarization_error()
        if error_name == 'p_bitflip_error': return ErrorsConf.generate_bitflip_error()
        if error_name == 'p_alice_phaseflip_error': return ErrorsConf.generate_alice_phase_flip_error()
        if error_name == 'p_bob_phaseflip_error': return ErrorsConf.generate_bob_phase_flip_error()
        if error_name == 'p_excited_mixture_error': return ErrorsConf.generate_excited_mixture_error()
        if error_name == 'p_excited_superposition_error': return ErrorsConf.generate_excited_superposition_error()

    @staticmethod
    def get_errors():
        return [
            'p_classical_error',
            'p_depol_error',
            'p_bitflip_error',
            'p_alice_phaseflip_error',
            'p_bob_phaseflip_error',
            'p_excited_mixture_error',
            'p_excited_superposition_error',
        ]

    def __init__(self, name: str, H_type: type, OB_types: list[type], alice_bases: list[AliceBase], Ns: list[int]):
        self.name = name
        self.H_type = H_type
        self.OB_types = OB_types
        self.alice_bases = alice_bases
        self.Ns = Ns
