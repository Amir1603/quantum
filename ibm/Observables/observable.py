from qiskit import QuantumCircuit
import math
import numpy as np
import utils
from conf import Conf

class Observable:
    def __init__(self, name, conf: Conf):
        self.name = name
        self.h = conf.h
        self.k = conf.k
        self.theta = conf.theta
        self.N = conf.N

    # --- Circuit Construction Methods (Keep as abstract or implement common logic) ---
    def apply_alice_measurement(self, qc: QuantumCircuit, alice_qubit, alice_creg):
        raise NotImplementedError()

    def apply_bob_operation(self, qc: QuantumCircuit, bob_qubit, alice_creg, xor_alice_res):
        raise NotImplementedError()

    def get_bob_measurement_basis(self):
        """Return 'X', 'Y', or 'Z' (or list for multi-qubit)"""
        raise NotImplementedError()

    def get_value(self, bitstring: str):
        """Calculate the observable's value for a given measurement bitstring."""
        raise NotImplementedError()

    def apply_ground_state(self, qc: QuantumCircuit, qubits: list):
        """
        Prepares the ground state for Charge.
        """
        denominator = np.sqrt(self.h**2 + self.k**2)

        if denominator == 0:
            raise ZeroDivisionError("h=k=0 - cannot calculate TFIM g.s.")

        # Ground state angle calculation parameter
        gs_theta = -np.arccos(
            (1 / np.sqrt(2)) * np.sqrt(1 - self.h / denominator)
        )
        # Apply Ry(2*gs_theta) for state preparation
        qc.ry(2 * gs_theta, qubits[utils.get_alice_qubit_idx(self.N)])
        qc.cx(qubits[utils.get_alice_qubit_idx(self.N)], qubits[utils.get_bob_qubit_idx(self.N)])


    def get_gs_expectation_value(self):
        # TODO: For simplicity currently this is the easiest way to add this functionality
        return 0

    # --- Post-Processing Calculations ---
    def calculate_expectation_and_sem(self, counts: dict, total_shots: int):
        """
        Calculates the expectation value and Standard Error of the Mean (SEM).
        Uses the get_value() method specific to the observable subclass.
        """
        if not counts or total_shots == 0:
            return 0.0, 0.0

        sum_val = 0.0
        sum_val_sq = 0.0

        for bitstring, count in counts.items():
            value = self.get_value(bitstring)
            sum_val += value * count
            sum_val_sq += (value**2) * count


        if total_shots <= 0:
             return 0.0, 0.0

        # Calculate expectation value <O>
        expectation = sum_val / total_shots
        expectation = expectation - self.get_gs_expectation_value()

        # Calculate <O^2>
        expectation_sq = sum_val_sq / total_shots

        # Calculate variance: Var(O) = <O^2> - <O>^2
        variance = max(0.0, expectation_sq - expectation**2)

        # Calculate SEM = sqrt(Var(O) / N)
        sem = math.sqrt(variance / total_shots) if total_shots > 0 else 0.0

        return expectation, sem

    def calculate_susceptibility(self, counts: dict):
        """Calculate susceptibility (often variance). Default: None."""
        # Default implementation returns None. Subclasses override if applicable.
        # Variance calculation is part of SEM, could reuse parts.
        total_shots = sum(counts.values())
        if not counts or total_shots == 0:
            return None

        sum_val = 0.0
        sum_val_sq = 0.0
        for bitstring, count in counts.items():
             try:
                value = self.get_value(bitstring)
                sum_val += value * count
                sum_val_sq += (value**2) * count
             except (KeyError, IndexError, ValueError):
                 total_shots -= count # Adjust as in SEM calc

        if total_shots <= 0: return None

        expectation = sum_val / total_shots
        expectation_sq = sum_val_sq / total_shots
        variance = max(0.0, expectation_sq - expectation**2)
        return variance # Default susceptibility definition as variance

    # --- Metadata ---
    def description(self):
        """Return a string description of the observable."""
        raise NotImplementedError()
