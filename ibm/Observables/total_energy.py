from .observable import Observable


class TotalEnergy(Observable):
    """
    A derived observable representing H_B = H1 + V.
    It does not correspond to a direct circuit execution but is calculated
    from the results of H1 and V.
    """
    def __init__(self, conf):
        super().__init__("total_energy", conf)
        self.component_observables = ["h1", "v"] # Names of observables it's derived from

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

    def calculate_susceptibility(self, counts: dict):
         raise NotImplementedError("TotalEnergy susceptibility requires combined analysis.")


    # --- Metadata ---
    def description(self):
        return "Derived H_B = H1 + V"

    @staticmethod
    def is_derived_observable():
        return True

    def get_component_names(self):
        return self.component_observables
