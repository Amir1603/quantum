import math
import numpy as np
from .observable import Observable

class TotalEnergy(Observable):
    """
    A derived observable representing H_B = h*Z1 + 2k*X0X1 for N=2 TFIM.
    It does not correspond to a direct circuit execution but is calculated
    from the results of H1_B and V_AB.
    """
    def __init__(self, conf):
        # Ensure N=2 for this observable
        if conf.N != 2:
             raise ValueError("TotalEnergy observable is defined for N=2 only.")
        super().__init__("total_energy", conf)
        self.component_observables = ["h1", "v"]

    # --- No Circuit Methods Needed ---
    def apply_ground_state(self, qc, qubits): pass
    def apply_alice_measurement(self, qc, alice_qubit, alice_creg): pass
    def apply_bob_operation(self, qc, bob_qubit, alice_creg, xor_alice_res): pass
    def get_bob_measurement_basis(self): return None # Not directly measured

    # --- Value Extraction (Not Applicable from Bitstring) ---
    def get_value(self, bitstring: str):
        raise NotImplementedError("TotalEnergy is derived, not calculated from single bitstring.")

    # --- Post-Processing Calculations (Not Applicable Directly) ---
    def calculate_expectation_and_sem(self, counts: dict, total_shots: int):
        raise NotImplementedError("TotalEnergy is derived from H1 and V results.")

    def calculate_derived_value_and_sem(self, component_results: dict):
        """
        Calculates the TotalEnergy value and SEM from component results.
        Args:
            component_results (dict): {'h1': RunResult for H1_B, 'v': RunResult for V_AB}
                                       (Keys must match self.component_observables)
        Returns:
            tuple: (final_value, final_sem) or (None, None) if calculation fails.
        """
        h1_res = component_results.get("h1")
        v_res = component_results.get("v")

        # Validate required components and their data
        if not h1_res or not v_res or \
           h1_res.expectation_value is None or v_res.expectation_value is None or \
           h1_res.sem is None or v_res.sem is None:
            # Optional: Add more specific print warnings
            # print(f"Warning: Missing component data for derived observable {self.name}")
            return None, None

        # Get h and k parameters from conf stored in one of the results
        # Use getattr for safety in case conf object structure changes
        h = h1_res.conf_params.get('h_param', h1_res.conf_params.get('h'))
        k = h1_res.conf_params.get('k_param', h1_res.conf_params.get('k'))

        if h is None or k is None:
             print(f"Warning: Missing h or k parameters in component results for {self.name}.")
             return None, None

        # Calculate combined expectation value: h * <h1_b> + 2 * k * <v_ab>
        exp_val_h1 = h1_res.expectation_value
        exp_val_v = v_res.expectation_value
        total_exp_val = h * exp_val_h1 + 2 * k * exp_val_v

        # Calculate ground state energy offset for N=2 TFIM (as previously done)
        # gs_energy = -(h**2 + 2*k**2) / math.sqrt(h**2 + k**2) # Original formula
        # Alternative based on shifted Hamiltonians: E_gs = -(C1 + C1 + C2)
        # Let's stick to the formula used previously in results.py for consistency
        denominator_gs = math.sqrt(h**2 + k**2) # Denominator for C1, C2 definition
        if denominator_gs == 0:
            gs_energy = 0.0 # Avoid division by zero if h=k=0
            print("Warning: h=k=0, ground state energy calculation skipped.")
        else:
            # Note: The previous code used sqrt(h^2+k^2) in the denominator,
            # which relates to C1 and C2. Let's re-evaluate the target value.
            # If H' = H + C1 + C2, then <H'>_gs = <H>_gs + C1 + C2.
            # The QET paper implies E_B = <H_B'> - <H_B'>_gs, where <H_B'>_gs = 0.
            # So E_B = <H_B'> = <H_B> + C1 + C2.
            # Let's calculate E_B relative to the *unshifted* ground state energy <H>_gs.
            # <H>_gs = -sqrt(h^2 + k^2) # This seems incorrect, TFIM GS energy is more complex.
            # Let's calculate E_B = <H_B> - <H_B>_gs as planned in N=3 case.
            # Need <H_B>_gs = <2k*X0X1 + h*Z1>_gs
            # <Z1>_gs = -h / sqrt(h^2+k^2)
            # <X0X1>_gs = -k / sqrt(h^2+k^2)
            # So, <H_B>_gs = 2k*(-k/sqrt(h^2+k^2)) + h*(-h/sqrt(h^2+k^2))
            # <H_B>_gs = -(h^2 + 2k^2) / sqrt(h^2+k^2)
            gs_energy_offset = -(h**2 + 2 * k**2) / denominator_gs

        # Calculate final value relative to ground state offset
        final_value = total_exp_val - gs_energy_offset

        # Calculate combined SEM for h*<h1> + 2k*<v>
        # SEM = sqrt( Var(h*O1 + 2k*O2) / shots )
        # Var(h*O1 + 2k*O2) ~ h^2*Var(O1) + (2k)^2*Var(O2) (assuming independence/low covariance)
        # SEM = sqrt( h^2*Var(O1)/shots + (2k)^2*Var(O2)/shots )
        # SEM = sqrt( h^2*SEM(O1)^2 + (2k)^2*SEM(O2)^2 )
        sem_h1 = h1_res.sem
        sem_v = v_res.sem
        total_sem = math.sqrt((h * sem_h1)**2 + (2 * k * sem_v)**2)

        return final_value, total_sem

    # --- Metadata ---
    def description(self):
        return "E_B = h*Z1 + 2k*X0X1 for N=2"

    @staticmethod
    def is_derived_observable():
        return True

    def get_component_names(self):
        return self.component_observables