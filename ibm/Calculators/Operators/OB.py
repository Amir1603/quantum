from .operator import Operator
from scipy.sparse import csc_matrix
from scipy.linalg import expm
import numpy as np
import utils

class BobOperator(Operator):
    def __init__(self, h, J, N, alice_base: str):
        super().__init__(h, J, N)

        self.alice_base = alice_base

        self.eta = None
        self.xi = None
        self.theta = None
        self.teleported_values = None
        self.probabilities = None

    def calc_eta_xi(self, gs_dm: np.ndarray):
        sigma_A = None
        sigma_B = None

        alice_idx = utils.get_alice_idx(self.N)
        bob_idx = utils.get_bob_idx(self.N)

        if self.alice_base == utils.AliceBase.X:
            sigma_A = utils.get_pauli_operator_on_site('X', alice_idx, self.N)
            sigma_B = utils.get_pauli_operator_on_site('Y', bob_idx, self.N)
        elif self.alice_base == utils.AliceBase.Y:
            sigma_A = utils.get_pauli_operator_on_site('Y', alice_idx, self.N)
            sigma_B = utils.get_pauli_operator_on_site('X', bob_idx, self.N)
        else:
            raise ValueError("Invalid Alice base. Use 'X' or 'Y'.")

        sigma_B_dot = 1j * (self.matrix @ sigma_B - sigma_B @ self.matrix)
        self.eta = np.trace(gs_dm @ sigma_A @ sigma_B_dot).real
        self.xi = np.trace(gs_dm @ sigma_B @ self.matrix @ sigma_B).real

    def calc_optimal_angle(self):
        self.theta = 0.5 * np.arctan2(self.eta, self.xi)

    def calc_teleported_values(self, gs_dm: np.ndarray, p_classical_comm_err: float):
        As = [False, True]
        self.teleported_values = {}

        alice_idx = utils.get_alice_idx(self.N)
        bob_idx = utils.get_bob_idx(self.N)

        for a in As:
            rho_B = csc_matrix((2**(self.N+1), 2**(self.N+1)), dtype=complex)

            for mu in [-1, 1]: # Alice's measurement outcome b
                I = utils.get_pauli_operator_on_site('I', alice_idx, self.N)
                sigma_A = utils.get_pauli_operator_on_site(self.alice_base, alice_idx, self.N)
                P_A = 0.5*(I + mu * sigma_A)

                bob_base = utils.AliceBase.X if self.alice_base == utils.AliceBase.Y else utils.AliceBase.Y
                sigma_B = utils.get_pauli_operator_on_site(bob_base, bob_idx, self.N)

                U_B = expm(-1j * mu * ((-1)**a) * self.theta * sigma_B.toarray())

                inner_part = P_A @ gs_dm @ P_A

                # Avoid excessive numerical calculation if it is redundant and no error applies
                if p_classical_comm_err != 0:
                    U_B_err = expm(-1j * mu * ((-1)**(not a)) * self.theta * sigma_B.toarray())
                    rho_B += (1-p_classical_comm_err) * U_B @ inner_part @ U_B.conj().T \
                            + p_classical_comm_err * U_B_err @ inner_part @ U_B_err.conj().T
                else:
                    rho_B += U_B @ inner_part @ U_B.conj().T

            self.teleported_values[a] = np.trace(rho_B @ self.matrix).real

    def calculate_final_probabilities(self, gs_dm: np.ndarray):
        """
        Calculates the final outcome probabilities for a=0 and a=1.
        This method is intended to be overridden by subclasses (like QB)
        that define specific projectors.
        """
        # This base implementation is a fallback, populating with NaNs
        # to signal it's not implemented, but preventing a crash.
        self.probabilities = {
            False: {'p_plus': np.nan, 'p_zero': np.nan, 'p_minus': np.nan},
            True:  {'p_plus': np.nan, 'p_zero': np.nan, 'p_minus': np.nan}
        }

    def calc_teleported_values_using_eta_xi(self):
        den = np.sqrt(self.eta**2 + self.xi**2)
        numerators = {
            True: self.eta**2 + self.xi**2,
            False: -self.eta**2 + self.xi**2
        }

        if den == 0:
            self.teleported_values = {
                a: 0.5*self.xi for a in numerators.keys()
            }
        else:
            self.teleported_values = {
                a: 0.5*(self.xi - num / den) for a, num in numerators.items()
            }

class HB(BobOperator):
    def __init__(self, h, J, N, alice_base):
        super().__init__(h, J, N, alice_base)

    def _build(self, int_site_idx: int):
        mat = csc_matrix((2**(self.N+1), 2**(self.N+1)), dtype=complex)

        bob_idx = utils.get_bob_idx(self.N)

        z_op = utils.get_pauli_operator_on_site('Z', bob_idx, self.N)
        xx_op = utils.get_multi_site_operator([('X', int_site_idx), ('X', bob_idx)], self.N)

        mat += self.h * z_op + self.J * xx_op

        return mat

class nn_HB(HB):
    def __init__(self, h, J, N, alice_base):
        super().__init__(h, J, N, alice_base)

    def _build_matrix(self):
        return self._build(utils.get_bob_neighbor_idx(self.N))

class alice_HB(HB):
    def __init__(self, h, J, N, alice_base):
        super().__init__(h, J, N, alice_base)

    def _build_matrix(self):
        return self._build(utils.get_alice_idx(self.N))

class QB(BobOperator):
    def __init__(self, h, J, N, alice_base):
        super().__init__(h, J, N, alice_base)
        self.projectors = self._build_projectors()

    def _build_matrix(self):
        bob_idx = utils.get_bob_idx(self.N)

        mat = csc_matrix((2**(self.N+1), 2**(self.N+1)), dtype=complex)

        i_op = utils.get_pauli_operator_on_site('I', bob_idx, self.N)
        z_op = utils.get_pauli_operator_on_site('Z', bob_idx, self.N)

        mat += 0.5*(i_op + z_op) # This is Pi_1 or |0><0|

        return mat

    def _build_projectors(self):
        """ Builds the projectors for the Z_N measurement outcomes """
        bob_idx = utils.get_bob_idx(self.N)
        i_op = utils.get_pauli_operator_on_site('I', bob_idx, self.N)
        z_op = utils.get_pauli_operator_on_site('Z', bob_idx, self.N)

        # Projector for Z_N = +1 (Eigenvalue 1 for QB)
        # Corresponds to p_plus in the security script
        pi_plus = 0.5 * (i_op + z_op) 

        # Projector for Z_N = -1 (Eigenvalue 0 for QB)
        # Corresponds to p_minus in the security script
        pi_minus = 0.5 * (i_op - z_op)

        return {'plus': pi_plus, 'minus': pi_minus}

    def calculate_final_probabilities(self, gs_dm: np.ndarray):
        """
        Calculates the final outcome probabilities for the QB observable.
        Maps QB eigenvalue 1 (Z_N = +1) to 'p_plus'.
        Maps QB eigenvalue 0 (Z_N = -1) to 'p_minus'.
        """
        As = [False, True] # a=0, a=1

        alice_idx = utils.get_alice_idx(self.N)
        bob_idx = utils.get_bob_idx(self.N)

        probs = {}

        for a in As:
            rho_B_a = csc_matrix((2**(self.N+1), 2**(self.N+1)), dtype=complex)

            for mu in [-1, 1]: # Alice's measurement outcome b
                I = utils.get_pauli_operator_on_site('I', alice_idx, self.N)
                sigma_A = utils.get_pauli_operator_on_site(self.alice_base, alice_idx, self.N)
                P_A = 0.5*(I + mu * sigma_A)

                bob_base = utils.AliceBase.X if self.alice_base == utils.AliceBase.Y else utils.AliceBase.Y
                sigma_B = utils.get_pauli_operator_on_site(bob_base, bob_idx, self.N)
                
                # Note: We use p_classical_comm_err = 0 for this analysis,
                # as quantum noise is passed in via gs_dm.
                U_B = expm(-1j * mu * ((-1)**a) * self.theta * sigma_B.toarray())

                inner_part = P_A @ gs_dm @ P_A
                rho_B_a += U_B @ inner_part @ U_B.conj().T

            # Calculate probabilities by tracing against projectors
            p_plus_1 = np.trace(rho_B_a @ self.projectors['plus']).real
            p_minus_1 = np.trace(rho_B_a @ self.projectors['minus']).real
            
            # Ensure probabilities sum to 1 (or close to it)
            norm = p_plus_1 + p_minus_1
            if not np.isclose(norm, 1.0, atol=1e-5):
                print(f"Warning: Probabilities for a={a} sum to {norm}, renormalizing.")
                if norm > 1e-9: # Avoid division by zero if norm is effectively zero
                    p_plus_1 /= norm
                    p_minus_1 /= norm
                else:
                    # Handle case where both probabilities are zero
                    p_plus_1 = 0.0
                    p_minus_1 = 0.0


            probs[a] = {
                'p_plus': p_plus_1,  # P(Z_N = +1), or P(QB = 1)
                'p_zero': 0.0,      # Z_N has no '0' outcome
                'p_minus': p_minus_1 # P(Z_N = -1), or P(QB = 0)
            }

        self.probabilities = probs
