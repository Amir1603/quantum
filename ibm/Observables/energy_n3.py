from .observable import Observable
from conf import Conf
import numpy as np

class Energy_N3(Observable):
    """
    A DERIVED observable representing Bob's Hamiltonian H_B = J*X1*X2 + Z2 for N=3.
    It also calculates the final teleported energy E_B = <H_B> - <H_B>_gs.
    Calculated from results of V_N3 (<X1X2>) and H1_N3 (<Z2>).
    """
    def __init__(self, conf: Conf, alice_basis: str):
        # Name reflects the final calculated value E_B and its parameters
        name = f"E_B_n3_alice{alice_basis.lower()}"
        super().__init__(name, conf) # Pass full conf
        self.alice_basis = alice_basis.upper()
        if self.N != 3: raise ValueError("Energy_N3 only supports N=3")

        # Define component names based on the naming convention used above
        self._v_n3_comp_name = f"qkd_v_n3_alice_{alice_basis.lower()}"
        self._h1_n3_comp_name = f"qkd_h1_n3_alice_{alice_basis.lower()}"
        self.component_observables = [self._v_n3_comp_name, self._h1_n3_comp_name]

        # --- Ground State Expectation Values ---
        # These MUST be calculated somehow (theoretically or separate runs)
        # Placeholder: Initialize to None, calculate in results processing
        self.exp_val_v_n3_gs = None
        self.exp_val_h1_n3_gs = None

    # --- No Circuit Methods Needed ---
    def apply_ground_state(self, qc): pass
    def apply_alice_measurement(self, qc, alice_qubit, alice_creg): pass
    def apply_bob_operation(self, qc, bob_qubit, alice_creg, xor_alice_res): pass
    def get_bob_measurement_basis(self): return None # Not directly measured

    # --- Value Extraction (Not Applicable from Bitstring) ---
    def get_value(self, bitstring: str):
        raise NotImplementedError(f"{self.name} is derived, not calculated from single bitstring.")

    # --- Post-Processing Calculations (Not Applicable Directly) ---
    def calculate_expectation_and_sem(self, counts: dict, total_shots: int):
        raise NotImplementedError(f"{self.name} is derived from component results.")

    # --- Metadata ---
    def description(self):
        return f"Derived E_B = <J*X1X2 + Z2> - <H_B>_gs for N=3 QKD (Alice: {self.alice_basis})"

    @staticmethod
    def is_derived_observable():
        return True

    def get_component_names(self):
        # Return names matching the V_N3 and H1_N3 instances for the specific Alice basis
        return self.component_observables

    def calculate_derived_value_and_sem(self, component_results: dict):
        """
        Calculates E_B = <H_B> - <H_B>_gs and its SEM.
        """
        v_res = component_results.get(self._v_n3_comp_name)
        h1_res = component_results.get(self._h1_n3_comp_name)

        if not v_res or not h1_res or \
        v_res.expectation_value is None or h1_res.expectation_value is None or \
        v_res.sem is None or h1_res.sem is None:
            print(f"Warning: Missing component data for derived observable {self.name}")
            return None, None

        j_val = self.k
        if j_val is None:
            print(f"Warning: J value is None for {self.name}. Cannot calculate derived value.")
            return None, None

        # Calculate <H_B> = J * <X1X2> + <Z2>
        exp_val_v = v_res.expectation_value
        exp_val_h1 = h1_res.expectation_value
        exp_val_hb = j_val * exp_val_v + exp_val_h1

        # Calculate SEM for <H_B>
        sem_v = v_res.sem
        sem_h1 = h1_res.sem
        sem_hb = np.sqrt((j_val * sem_v)**2 + sem_h1**2)

        # --- Calculate <H_B>_gs = J<X1X2>_gs + <Z2>_gs ---
        exp_X1X2_gs = self.calculate_gs_expectation("IXX") # Pauli string for X1*X2
        exp_Z2_gs = self.calculate_gs_expectation("IIZ") # Pauli string for Z2

        if exp_X1X2_gs is None or exp_Z2_gs is None:
            print(f"Warning: Failed to calculate ground state expectation values for H_B_gs (J={j_val}). Assuming 0.")
            hb_gs = 0.0
        else:
            hb_gs = j_val * exp_X1X2_gs + exp_Z2_gs
            print(f"Calculated <H_B>_gs for J={j_val}: {hb_gs:.4f} (J*{exp_X1X2_gs:.4f} + {exp_Z2_gs:.4f})")


        # Calculate final E_B = <H_B> - <H_B>_gs
        final_eb_value = exp_val_hb - hb_gs
        # SEM of the difference: SEM(<HB>) assuming SEM(<HB>_gs) is negligible (from numerical calc)
        final_eb_sem = sem_hb

        return final_eb_value, final_eb_sem