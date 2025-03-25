from conf import Conf
from constants import *
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp
from .observable import Observable

class Current(Observable):
    def __init__(self, conf: Conf, apply_protocol):
        self.apply_protocol = apply_protocol
        name = f'current{"" if apply_protocol else "_no_protocol"}'
        # NOTE: Defining a simple local operator for "current".
        # In theory, current is j ~ XY - YX. Measuring X is a common proxy.
        # We'll measure Bob in the X basis. The SparsePauliOp here is less critical
        # if we define the measurement basis and value extraction directly.
        # Let's define it formally as X for clarity.
        op_list = [("I" * conf.n_qubits, 0.0)] # Placeholder, will measure X basis directly
        op_list[0] = ("I" * BOB_QUBIT_IDX + "X" + "I" * (conf.n_qubits - BOB_QUBIT_IDX - 1), 1.0)
        super().__init__(name, SparsePauliOp.from_list(op_list), conf.h, conf.k)
        # Store h, k if needed for ground state, although ground state prep is often independent
        self.h = conf.h
        self.k = conf.k


    def apply_ground_state(self, qc: QuantumCircuit, qubits: list):
        """
        Prepares the ground state. Assumes the same TFIM ground state is used.
        Re-using the Charge implementation logic. Adjust if needed.
        """
        # Ensure h and k are non-zero before calculation if needed
        if self.h == 0 and self.k == 0:
             # Handle singularity or default case, e.g., simple Ry or H gates
             # For critical TFIM (h=J=1, k related to J), this calculation is likely valid
             pass # Assuming h, k are set for valid calculation below

        # Using the provided ground state prep method, ensure h,k are valid
        # Check for potential division by zero if h=k=0
        denominator = np.sqrt(self.h**2 + self.k**2)
        if denominator == 0:
             # Default rotation, e.g. corresponds to h=1, k=0 -> Ry(pi/2) -> |+> state? Check TFIM physics.
             # Or handle as an error. For the critical TFIM state from charge, use the fixed angle.
             theta = -3*np.pi/8 # Fixed angle for critical 2-qubit TFIM g.s.
             print("Warning: h=k=0, using fixed theta for critical TFIM g.s.")
        else:
            # Original formula from Charge class - verify this is correct for TFIM ground state
             theta = -np.arccos(
                 (1 / np.sqrt(2)) * np.sqrt(1 - self.h / denominator)
             )

        # Apply the gates (assuming 2 qubits for simplicity here, adjust for N)
        qc.ry(2 * theta, qubits[0])
        qc.cx(qubits[0], qubits[1])

    def apply_alice_measurement(self, qc: QuantumCircuit, alice_qubit, alice_creg):
        """
        Alice measures charge density (rho ~ Z).
        This means measuring in the Z basis directly.
        """
        qc.measure(alice_qubit, alice_creg) # Measure in Z basis

    def apply_bob_operation(self, qc: QuantumCircuit, bob_qubit, alice_creg):
        """
        Bob's operation depends on Alice's charge measurement (Z-basis: 0 or 1).
        We apply a conditional rotation related to current (e.g., Rx).
        Operation: U(a) = exp(-i * a * pi * X / 2) -> Rx(a * pi)
        where 'a' represents Alice's measurement outcome (+1 for '0', -1 for '1').
        We apply Rx(pi) if Alice measured '1'.
        """
        if self.apply_protocol:
            # Apply Rx(pi) if Alice measured '1'.
            # Rx(pi) flips |+> to |+> (via - -> +) and |-> to |-> (via + -> -), effectively applying a Z gate in the X basis.
            qc.rx(np.pi, bob_qubit).c_if(alice_creg, 1)
        else:
            pass  # No operation if protocol is not applied

    def get_bob_measurement_basis(self):
        """
        Bob measures in the X basis to measure a current-related observable (proxy: X).
        """
        return "X" # Measurement in X basis requires applying H before Z measurement

    def get_operator(self, site):
        """
        Returns the Pauli string for the measurement operator at the site.
        For current (proxy), Bob measures X.
        """
        if site == "bob":
            return "X"
        elif site == "alice":
            return "Z" # Alice measured Z
        else:
            raise ValueError("Invalid site specified")

    def get_value(self, bitstring: str):
        """
        Extracts the eigenvalue for Bob's X-basis measurement.
        Requires measuring Z basis *after applying H* to Bob's qubit.
        Simulator measurement applies H implicitly if basis 'X' is specified,
        or we apply H explicitly before a Z measurement.
        Assuming standard Z measurement result in bitstring corresponds to post-H state:
        - If measured '0' (state |+>_X): Eigenvalue is +1
        - If measured '1' (state |->_X): Eigenvalue is -1
        """
        # Ensure BOB_QUBIT_IDX and bitstring order convention are correct!
        try:
             # Use corrected index based on previous findings
             bob_measurement_result = bitstring[BOB_QUBIT_IDX] # CHECK YOUR INDEXING CONVENTION
        except IndexError:
             raise ValueError(f"Cannot access index {BOB_QUBIT_IDX} in bitstring '{bitstring}'")

        if bob_measurement_result == '0':
            return 1.0  # Eigenvalue +1 for |+>_X state
        else:
            return -1.0 # Eigenvalue -1 for |->_X state

    def description(self):
        return "X (current proxy)"

    # --- Methods below might need adjustment based on how you define/use them ---

    def get_bob_current_outcome(self, bitstring: str):
        """
        Extracts Bob's measurement outcome (+1 or -1) from the bitstring.
        """
        # Ensure BOB_QUBIT_IDX and bitstring order convention are correct!
        if bitstring[BOB_QUBIT_IDX] == '0':
             return 1 # Outcome corresponding to +1 eigenvalue
        else:
             return -1 # Outcome corresponding to -1 eigenvalue


    def calculate_susceptibility(self, counts):
        """
        Calculates susceptibility (variance) for the measured 'current' (X operator).
        """
        measurement_values = []
        total_shots = sum(counts.values())
        if total_shots == 0: return 0.0

        for bitstring, count in counts.items():
             # Use get_value which returns +1 or -1
            value = self.get_value(bitstring)
            measurement_values.extend([value] * count)

        # Variance = <O^2> - <O>^2. Since values are +/-1, O^2 is always 1.
        # So <O^2> = 1.
        mean_value = np.mean(measurement_values)
        variance = 1.0 - (mean_value**2)
        # Ensure non-negative due to potential floating point issues
        susceptibility = max(0.0, variance)
        return susceptibility

    def get_extra_info(self, counts):
        susceptibility = self.calculate_susceptibility(counts)
        return f"Current (X) susceptibility: {susceptibility}"