from utils import AliceBase
from Calculators import Operators
from conf import ErrorsConf
from plot_utils import PlotProperties


class RunConf:
    def __init__(self, name: str, H_type: type, OB_types: dict[str, type], alice_basis: AliceBase, N: int):
        self.name = name
        self.H_type = H_type
        self.OB_types = OB_types
        self.alice_basis = alice_basis
        self.N = N

        self.J_pps = {
            k: PlotProperties(
                f"{self.name}/{self.alice_basis}/N{self.N}/{k}_vs_J.png"
            ) for k in self.OB_types.keys()
        }
        self.h_pps = {
            k: PlotProperties(
                f"{self.name}/{self.alice_basis}/N{self.N}/{k}_vs_h.png", True
            ) for k in self.OB_types.keys()
        }
        self.errs_pps = {k: {e: PlotProperties(
                f"{self.name}/{self.alice_basis}/N{self.N}/{k}_vs_{e}.png"
            ) for e in NumericalRunConf.get_errors()} for k in self.OB_types.keys()}
        self.class_comm_errs_N_pps = {
            k: PlotProperties(
                f"{self.name}/{self.alice_basis}/{k}_vs_p_class_comm_err.png"
            ) for k in self.OB_types.keys()}

    def get_all_pps(self) -> list[PlotProperties]:
        """
        Returns a list of all PlotProperties objects for this RunConf.
        """
        pps = []

        pps.extend(self.J_pps.values())
        pps.extend(self.h_pps.values())
        [pps.extend(v.values()) for v in self.errs_pps.values()]

        return pps

class NumericalRunConf:
    @staticmethod
    def AliceConf():
        return NumericalRunConf(
            'alice',
            Operators.alice_H,
            {"energy": Operators.alice_HB, "charge": Operators.QB},
            [AliceBase.X],
            [1, 2, 3, 4]
        )

    @staticmethod
    def NNConf():
        return NumericalRunConf(
            'nn',
            Operators.nn_H,
            {"energy": Operators.nn_HB, "charge": Operators.QB},
            [AliceBase.X, AliceBase.Y],
            [2, 3, 4]
        )

    @staticmethod
    def get_ylim(error_name: str, obs_name: str, H_type: type):
        if obs_name == 'energy':
            if H_type == Operators.alice_H:
                if error_name == 'p_bitflip_error': return (-0.1, 0.5)
                if error_name == 'p_alice_phaseflip_error': return (-0.1, 0.5)
                if error_name == 'p_bob_phaseflip_error': return (-0.1, 0.5)
                if error_name == 'p_excited_mixture_error': return (-0.1, 0.2)
                if error_name == 'p_excited_superposition_error': return (-0.1, 0.2)
            elif H_type == Operators.nn_H:
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
    def generate_class_comm_error_Ns(name: str) -> list[int]:
        Ns = [2, 3, 4, 5, 6, 7, 8, 9, 10]
        if name == 'alice':
            Ns = [1] + Ns

        return Ns

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

    def __init__(self, name: str, H_type: type, OB_types: dict[str, type], alice_bases: list[AliceBase], Ns: list[int]):
        self.confs = [RunConf(name, H_type, OB_types, alice_base, N)
                      for alice_base in alice_bases
                      for N in Ns]
