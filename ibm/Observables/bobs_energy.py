from .observable import Observable
from Calculators.tfim_calculator import TFIMCalculator
from conf import Conf
import utils
import numpy as np

class BobsEnergy(Observable):
    """
    A derived observable representing Bob's Hamiltonian H_B = J*X*X + h*Z.
    It doesn't correspond to a direct circuit execution, but is calculates the final
    teleported energy in arbitrary units E_B = (<H_B> - <H_B>_gs)/<H_B>_gs.
    Calculated from results of V (<XX>) and H1 (<Z>).
    """
    def __init__(self, conf: Conf, calc: TFIMCalculator):
        name = "E_B"
        super().__init__(name, conf, calc)

        self._h1_comp_name = "H1_B"
        self._v_comp_name = "V_B"
        self.component_observables = [self._v_comp_name, self._h1_comp_name]

    # --- Value Extraction (Not Applicable from Bitstring) ---
    def get_value(self, bitstring: str):
        raise NotImplementedError(f"{self.name} is derived, not calculated from single bitstring.")

    # --- Post-Processing Calculations (Not Applicable Directly) ---
    def calculate_expectation_and_sem(self, counts: dict, total_shots: int):
        raise NotImplementedError(f"{self.name} is derived from component results.")

    # --- Metadata ---
    def description(self):
        bob_idx = utils.get_bob_idx(self.N)
        alice_idx = utils.get_alice_idx(self.N)

        return f"Derived E_B = <J*X{alice_idx}X{bob_idx} + Z{bob_idx}> - <H_B>_gs for N={self.N}"

    @staticmethod
    def is_derived_observable():
        return True

    def get_component_names(self):
        return self.component_observables

    def calculate_derived_value_and_sem(self, component_results: dict):
        """
        Calculates the Bob's energy value and SEM from component results.
        Args:
            component_results (dict): {'h1': RunResult for H1_B, 'v': RunResult for V_B}
                                       (Keys must match self.component_observables)
        Returns:
            tuple: (final_value, final_sem) or (None, None) if calculation fails.
        """
        h1_res = component_results.get(self._h1_comp_name)
        v_res = component_results.get(self._v_comp_name)

        # Validate required components and their data
        if not h1_res or not v_res or \
           h1_res.expectation_value is None or v_res.expectation_value is None or \
           h1_res.sem is None or v_res.sem is None:
            print(f"Warning: Missing component data for derived observable {self.name}")
            return None, None

        # Get h and J parameters from conf stored in one of the results
        h = h1_res.conf_params.get('h')
        J = h1_res.conf_params.get('J')

        if h is None or J is None:
             print(f"Warning: Missing h or J parameters in component results for {self.name}.")
             return None, None

        if (self.h, self.J) != (h, J):
            return None, None

        # Calculate combined expectation value: h * <h1_b> + J * <V>
        exp_val_h1 = h1_res.expectation_value
        exp_val_v = v_res.expectation_value
        exp_val_hb = h * exp_val_h1 + J * exp_val_v

        gs_energy = self._calc.bob_energy

        # Calculate final value relative to ground state in arbitrary units
        final_value = (exp_val_hb - gs_energy) / abs(gs_energy)

        # Calculate combined SEM for h*<h1> + J*<V>
        sem_h1 = h1_res.sem
        sem_v = v_res.sem
        total_sem = np.sqrt((h * sem_h1)**2 + (J * sem_v)**2)

        return final_value, total_sem
