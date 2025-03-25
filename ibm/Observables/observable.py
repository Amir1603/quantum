from qiskit import QuantumCircuit


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

    def get_value(self, bitstring: str):
        raise NotImplementedError()

    def get_operator(self, site):
        raise NotImplementedError()

    def description(self):
        raise NotImplementedError()

    def get_extra_info(self, counts):
        return ""