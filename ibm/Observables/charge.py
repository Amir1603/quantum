from qiskit import QuantumCircuit
from .observable import Observable
from Calculators.tfim_calculator import TFIMCalculator
from conf import QuantumSimConf
import utils

class Charge(Observable):
    """
    Observable for Bob's local charge density (rho_B ~ (I+Z)/2) for arbitrary N,
    under the protocol optimized for energy (Alice measures X, Bob rotates Ry based on theta).
    """
    def __init__(self, conf: QuantumSimConf, alice_basis: utils.AliceBase, calc: TFIMCalculator):
        name = f'charge'
        super().__init__(name=name, conf=conf, alice_basis=alice_basis, calc=calc)

    def apply_alice_measurement(self, qc: QuantumCircuit):
        alice_idx = utils.get_alice_idx(self.N)
        utils.apply_basis(qc, self._alice_basis, alice_idx)

    # TODO: What is the different from energy? Can the operation be unified?
    def apply_bob_operation(self, qc: QuantumCircuit, xor_res):
        """
        Bob's conditional operation based on Alice's measurement (outcome c).
        Operation is U_B(a) = Ry(a*theta), where a=+1 (c=0) or a=-1 (c=1).
        """
        alice_idx = utils.get_alice_idx(self.N)
        bob_idx = utils.get_bob_idx(self.N)

        theta = self._calc.ops['QB'].theta

        # Apply the controlled rotation based on Alice's measurement.
        # `if_test` is not supported on real hardware, andfor some reason `c_if` is not working.
        # => We use a workaround suggested by Kazuki.
        angle = -2 * theta if xor_res == 0 else 2 * theta

        # If Alice's basis is 'X', Bob uses 'Y' rotation and vice versa.
        if self._alice_basis == utils.AliceBase.X:
            # Apply the controlled rotation based on Alice's measurement.
            # `if_test` is not supported on real hardware, andfor some reason `c_if` is not working.
            # => We use a workaround suggested by Kazuki.
            qc.cry(angle, alice_idx, bob_idx)
            qc.x(alice_idx)
            qc.cry(-angle, alice_idx, bob_idx)
            qc.x(alice_idx)
        elif self._alice_basis == utils.AliceBase.Y:
            qc.crx(angle, alice_idx, bob_idx)
            qc.x(alice_idx)
            qc.crx(-angle, alice_idx, bob_idx)
            qc.x(alice_idx)
        else:
            raise ValueError(f"Unsupported Alice basis '{self._alice_basis}'.")

        # This is equivalent to:
        ### with qc.if_test((alice_idx, 0^xor_alice_res)):
        ###     qc.ry(-2 * theta, bob_idx)
        ### with qc.if_test((alice_idx, 1^xor_alice_res)):
        ###     qc.ry(2 * theta, bob_idx)

    def get_bob_measurement_basis(self):
        """
        Bob measures charge density rho = (I + Z) / 2. Requires Z basis.
        """
        return "Z"

    def get_value(self, bitstring: str):
        """
        Extracts the eigenvalue for Bob's charge density operator rho = (I + Z) / 2.
        rho|+> = 1|+> (Eigenvalue 1, measurement '0')
        rho|-> = 0|-> (Eigenvalue 0, measurement '1')
        """
        bob_idx = utils.get_bob_idx(self.N)
        bob_measurement_bit = utils.get_bit_from_counts(bitstring, bob_idx, self.N+1)

        if bob_measurement_bit == '0':
            return 1.0 # Z eigenvalue +1 -> charge density eigenvalue 1
        else:
            return 0.0 # Z eigenvalue -1 -> charge density eigenvalue 0

    def get_theoretical_gs_expectation_value(self):
        return self._calc.ops['QB'].gs_expectation

    def description(self):
        bob_idx = utils.get_bob_idx(self.N)
        return f"Bob's Charge Density (I+Z{bob_idx})/2"