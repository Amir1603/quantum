from conf import Conf
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp


class Observable:
    def __init__(self, name, expression, h, k):
        self.name = name
        self.expression = expression
        self.h = h
        self.k = k

    def apply_ground_state(self, qc: QuantumCircuit, qubits: list):
        raise NotImplementedError()

    def apply_alice_measurement(self, qc: QuantumCircuit, alice_qubit, alice_creg):
        raise NotImplementedError()

    def apply_bob_operation(self, qc: QuantumCircuit, bob_qubit, alice_creg):
        raise NotImplementedError()

    def get_bob_measurement_basis(self):
        raise NotImplementedError()

    def get_operator(self, site):
        raise NotImplementedError()

    def description():
        raise NotImplementedError()


class Energy(Observable):
    def __init__(self, name, expression, h, k):
        super().__init__(name, expression, h, k)

    def apply_ground_state(self, qc: QuantumCircuit, qubits: list):
        """
        Prepares the ground state for Energy.
        """
        theta = -np.arccos(
            (1 / np.sqrt(2)) * np.sqrt(1 - self.h / np.sqrt(self.h**2 + self.k**2))
        )
        qc.ry(2 * theta, qubits[0])
        qc.cx(qubits[0], qubits[1])

    def apply_alice_measurement(self, qc: QuantumCircuit, alice_qubit, alice_creg):
        """
        Alice's measurement for Energy.
        """
        qc.h(alice_qubit)  # Apply Hadamard to ancillary qubit
        qc.measure(alice_qubit, alice_creg)

    def apply_bob_operation(self, qc: QuantumCircuit, bob_qubit, alice_creg):
        """
        Bob's conditional operation for Energy.
        """
        phi = np.arcsin(
            (self.h * self.k) / np.sqrt((self.h**2 + 2 * self.k**2)**2 + self.h**2 * self.k**2)
        ) / 2
        qc.ry(2 * phi, bob_qubit).c_if(alice_creg, 0)
        qc.ry(-2 * phi, bob_qubit).c_if(alice_creg, 1)

    def get_operator(self, site):
        """
        Returns the operator string for Energy.
        """
        if site == "alice":
            return "Z"  # Or "ZI" if needed
        elif site == "bob":
            return "Z"
        else:
            raise ValueError("Invalid site specified")


class H1(Energy):
    def __init__(self, conf: Conf):
        super().__init__("h1",
                         SparsePauliOp.from_list([
                             ("ZI", conf.h),
                             ("II", conf.h**2 / np.sqrt(conf.h**2 + conf.k**2))
                            ]),
                         conf.h,
                         conf.k)

    def get_bob_measurement_basis(self):
        return "Z"

    def is_positive_count(self, bitstring: str) -> bool:
        return bitstring[1] == '0' # Check the second bit for <H1>

    def description():
        return "Z (H1)"


class V(Energy):
    def __init__(self, conf: Conf):
        super().__init__("v",
                         SparsePauliOp.from_list([
                             ("XX", 2 * conf.k),
                             ("II", 2 * conf.k**2 / np.sqrt(conf.h**2 + conf.k**2))
                             ]),
                         conf.h,
                         conf.k)

    def get_bob_measurement_basis(self):
        return "X"

    def is_positive_count(self, bitstring: str) -> bool:
        return bitstring in ('11', '00')

    def description():
        return "XX (V)"


class Charge(Observable):
    def __init__(self, conf: Conf):
        super().__init__("charge", SparsePauliOp.from_list([
            ("II", 0.5),
            ("ZI", 0.5),
            ("IZ", 0.5),
            ("ZZ", 0.5)
        ]),
        conf.h,
        conf.k)

    def apply_ground_state(self, qc: QuantumCircuit, qubits: list):
        """
        Prepares the ground state for Charge.
        """
        theta = -np.arccos(
            (1 / np.sqrt(2)) * np.sqrt(1 - self.h / np.sqrt(self.h**2 + self.k**2))
        )
        qc.ry(2 * theta, qubits[0])
        qc.cx(qubits[0], qubits[1])

    def apply_alice_measurement(self, qc: QuantumCircuit, alice_qubit, alice_creg):
        """
        Alice measures the chirality using the projection operator P(b) = 1/2 (1 - (-1)^b X)
        This is equivalent to measuring in the X basis.
        """
        qc.h(alice_qubit)  # Apply Hadamard to measure in X basis
        qc.measure(alice_qubit, alice_creg)

    def apply_bob_operation(self, qc: QuantumCircuit, bob_qubit, alice_creg):
        """
        Bob's operation is a conditional Ry rotation: U(b) = exp(-b i Y) = Ry(-2b)
        """
        phi = np.arcsin(
            (self.h * self.k) / np.sqrt((self.h**2 + 2 * self.k**2)**2 + self.h**2 * self.k**2)
        ) / 2
        qc.ry(-2 * np.pi, bob_qubit).c_if(alice_creg, 0)  # b=0: Ry(0) = I (no rotation)
        qc.ry(2 * np.pi, bob_qubit).c_if(alice_creg, 1)  # b=1: Ry(-2pi)

    def get_bob_measurement_basis(self):
        """
        Bob measures in the Z basis to measure the charge density operator (I + Z) / 2
        """
        return "Z"

    def get_operator(self, site):
        """
        For a single site, the charge density operator is (I + Z) / 2.
        The eigenvalue is 1 if the measurement is 0, and 0 if the measurement is 1.
        """
        if site == "alice" or site == "bob":
            return "Z"
        else:
            raise ValueError("Invalid site specified")

    def is_positive_count(self, bitstring: str) -> bool:
        """
        For a single site, the charge density operator is (I + Z) / 2.
        The eigenvalue is 1 if the measurement is 0, and 0 if the measurement is 1.
        We consider '0' as the positive outcome.
        """
        return bitstring == '0'

    def description():
        return "I+Z (J_0)"


class Current(Observable):
    def __init__(self, conf: Conf):
        super().__init__("current", SparsePauliOp.from_list([
            ("XI", 0.5),
            ("X", -0.5),
            ("IX", 0.5),
            ("ZX", -0.5)
        ]),
        conf.h,
        conf.k)

    def apply_ground_state(self, qc: QuantumCircuit, qubits: list):
        """
        Prepares the ground state for Current.
        """
        theta = -np.arccos(
            (1 / np.sqrt(2)) * np.sqrt(1 - self.h / np.sqrt(self.h**2 + self.k**2))
        )
        qc.ry(2 * theta, qubits[0])
        qc.cx(qubits[0], qubits[1])

    def apply_alice_measurement(self, qc: QuantumCircuit, alice_qubit, alice_creg):
        """
        Alice measures the chirality using the projection operator P(b) = 1/2 (1 - (-1)^b X)
        This is equivalent to measuring in the X basis.
        """
        qc.h(alice_qubit)
        qc.measure(alice_qubit, alice_creg)

    def apply_bob_operation(self, qc: QuantumCircuit, bob_qubit, alice_creg):
        """
        Bob's operation is a conditional Ry rotation: U(b) = exp(-b i Y) = Ry(-2b)
        """
        phi = np.arcsin(
            (self.h * self.k) / np.sqrt((self.h**2 + 2 * self.k**2)**2 + self.h**2 * self.k**2)
        ) / 2
        qc.ry(-2 * np.pi, bob_qubit).c_if(alice_creg, 0)  # b=0: Ry(0) = I
        qc.ry(2 * np.pi, bob_qubit).c_if(alice_creg, 1)  # b=1: Ry(-2pi)

    def get_bob_measurement_basis(self):
        """
        Bob measures in the X basis. The current operator involves X and Z.
        We measure in the X basis to get the expectation value of X.
        """
        return "X"

    def get_operator(self, site):
        """
        The current operator is X(I-Z)/2. The eigenvalue of X is +1 or -1.
        """
        if site == "alice" or site == "bob":
            return "X"
        else:
            raise ValueError("Invalid site specified")

    def is_positive_count(self, bitstring: str) -> bool:
        """
        The current operator is X(I-Z)/2. The eigenvalue of X is +1 or -1.
        We consider the +1 outcome as the positive outcome.
        """
        return bitstring == '0'

    def description():
        return "X*(I-Z) (J_1)"

def create_observables(conf: Conf) -> list[Observable]:
        return [H1(conf), V(conf)]