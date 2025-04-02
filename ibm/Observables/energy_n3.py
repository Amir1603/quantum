import numpy as np
from qiskit import QuantumCircuit, ClassicalRegister
from .observable import Observable
import utils
from conf import Conf
from qiskit.quantum_info import SparsePauliOp # Import needed

class Energy_N3(Observable):
    """
    Observable for simulating the N=3 QKD protocol from the paper.
    It sets up the circuit according to Alice's basis choice.
    The final E_B calculation requires post-processing of expectation values.
    """
    def __init__(self, conf: Conf, alice_basis: str):
        # Name distinguishes between Alice's X or Y measurement choice
        super().__init__(f"energy_n3_alice_{alice_basis.lower()}", conf)
        self.alice_basis = alice_basis.upper() # Store as 'X' or 'Y'
        if self.N != 3:
            raise ValueError("Energy_N3 only supports N=3")
        if self.alice_basis not in ['X', 'Y']:
            raise ValueError("Alice basis must be 'X' or 'Y'")

        # Define Bob's Hamiltonian H_B = J*X1*X2 + Z2 as SparsePauliOp
        # Qiskit orders qubits right-to-left (q2, q1, q0)
        # X1*X2 -> 'IXX', Z2 -> 'IIZ'
        self.H_B_op = SparsePauliOp.from_list([
            ("IXX", self.J_param), # J * X1*X2
            ("IIZ", 1.0)          # 1 * Z2
        ])

        # Pre-calculate ground state expectation E_B_gs = <gs|H_B|gs>
        gs_vector = self._get_n3_tfim_ground_state() # Use method from base class
        # Need the operator matrix for <psi|Op|psi> calculation
        # Note: Using statevector simulation here for simplicity.
        # In a real experiment, E_B_gs would also be estimated via measurements.
        try:
             from qiskit.quantum_info import Statevector
             self.E_B_gs = Statevector(gs_vector).expectation_value(self.H_B_op).real
             print(f"Calculated E_B_gs = {self.E_B_gs} for J={self.J_param}")
        except Exception as e:
             print(f"Could not calculate E_B_gs analytically: {e}. Setting to 0.")
             self.E_B_gs = 0.0


    def apply_alice_measurement(self, qc: QuantumCircuit, alice_qubit_idx: int, alice_creg):
        """Alice measures site 0 in X or Y basis. Adds measurement."""
        if self.alice_basis == 'X':
            qc.h(alice_qubit_idx)
        elif self.alice_basis == 'Y':
            # qc.sdg(alice_qubit_idx) # Measure Y = H.Sdg.Z.H = Rz(-pi/2).H.Z.H
            # To measure in Y basis: Apply Sdg, then H, then measure Z
            qc.sdg(alice_qubit_idx)
            qc.h(alice_qubit_idx)
        qc.measure(alice_qubit_idx, alice_creg) # Measure Z after basis change

    def apply_bob_operation(self, qc: QuantumCircuit, bob_qubit_idx: int, alice_creg, xor_alice_res: int):
        """
        Bob's conditional rotation on site 2 (index N-1 = 2).
        U_B = exp(-i*theta*(-1)^c * sigma_B) where c = measured_bit XOR xor_alice_res.
        sigma_B = Y2 if Alice measured X0.
        sigma_B = X2 if Alice measured Y0.
        """
        # Theta calculation (Eq 10, 11) is complex, depends on <gs|...|gs>.
        # For simplicity, using a fixed or configurable theta here.
        # Let's assume theta is optimal (e.g., pi/4 or a value found numerically)
        # Or use the self.theta from conf if provided.
        protocol_theta = self.theta if self.theta is not None else np.pi / 4 # Example placeholder

        bob_op_basis = 'Y' if self.alice_basis == 'X' else 'X'

        # Apply operation based on Alice's classical register bit `alice_creg`
        # If (alice_creg XOR xor_alice_res) == 0 -> apply Rotation(2*theta)
        # If (alice_creg XOR xor_alice_res) == 1 -> apply Rotation(-2*theta)
        angle_if_0 = 2 * protocol_theta
        angle_if_1 = -2 * protocol_theta

        print(f"Applying Bob Op: Basis={bob_op_basis}, Theta={protocol_theta:.3f}, XOR={xor_alice_res}")

        if bob_op_basis == 'Y':
            with qc.if_test((alice_creg, 0 ^ xor_alice_res)): # Condition if bit is 0 after XOR
                 qc.ry(angle_if_0, bob_qubit_idx)
            with qc.if_test((alice_creg, 1 ^ xor_alice_res)): # Condition if bit is 1 after XOR
                 qc.ry(angle_if_1, bob_qubit_idx)
        elif bob_op_basis == 'X':
            with qc.if_test((alice_creg, 0 ^ xor_alice_res)):
                 qc.rx(angle_if_0, bob_qubit_idx)
            with qc.if_test((alice_creg, 1 ^ xor_alice_res)):
                 qc.rx(angle_if_1, bob_qubit_idx)

    def get_bob_measurement_basis(self):
        """
        Returns the observable (H_B) to be measured by the Estimator.
        """
        return self.H_B_op # Return the SparsePauliOp for H_B

    def get_value(self, bitstring: str):
        """Not directly used if using Estimator for H_B expectation."""
        raise NotImplementedError("Energy_N3 uses Estimator for <H_B>")

    def calculate_expectation_and_sem(self, counts: dict, total_shots: int):
        """
        This observable relies on the Estimator output and post-processing
        in results.py to get the final E_B. This method shouldn't be called directly
        for the final E_B value.
        """
        print("Warning: calculate_expectation_and_sem called on Energy_N3. Final E_B is calculated in Results.process_results.")
        # Return dummy value or maybe expectation of a single term if needed elsewhere
        return 0.0, 0.0

    def description(self):
        return f"Energy for N=3 (Alice Basis: {self.alice_basis}, J={self.k})"
