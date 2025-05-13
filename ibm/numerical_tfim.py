import numpy as np
from scipy.sparse import kron, eye, csc_matrix
from scipy.sparse.linalg import eigsh
import utils

class NumericalTFIM:
    # Pauli Matrices
    I = csc_matrix(np.array([[1, 0], [0, 1]], dtype=complex))
    X = csc_matrix(np.array([[0, 1], [1, 0]], dtype=complex))
    Y = csc_matrix(np.array([[0, -1j], [1j, 0]], dtype=complex))
    Z = csc_matrix(np.array([[1, 0], [0, -1]], dtype=complex))

    def __init__(self, N, J, h):
        """
        Initialize the NumericalTFIM class with parameters for the transverse field Ising model.

        Parameters:
        N (int): Number of spins.
        J (float): Coupling constant.
        h (float): Transverse field strength.
        """
        self.N = N
        self.J = J
        self.h = h
        self.H = self._build_tfim_hamiltonian()

    def calc_all(self):
        """
        Calculate the ground state, first excited state, and their properties.
        Returns:
        tuple: Ground state energy, ground state vector, first excited state energy, first excited state vector,
               density matrix of the ground state, total energy, total charge,
               expectation values of Z and XX operators.
        """
        self.E0, self.gs0, self.E1, self.ex1 = self._compute_lowest_states()

        # Compute density matrices
        self.gs_rho = NumericalTFIM._compute_density_matrix(self.gs0)
        self.ex1_rho = NumericalTFIM._compute_density_matrix(self.ex1)

        self.total_energy, self.total_charge = self._compute_gs_total_energy_and_charge()
        self.bob_energy, self.bob_charge = self._compute_bob_gs_energy_and_charge()
        self.theta_E1, self.theta_E2, self.theta_q1, self.theta_q2 = self._compute_optimal_rotation_angles()

    # Hamiltonian Construction for TFIM
    def _build_tfim_hamiltonian(self):
        H = csc_matrix((2**self.N, 2**self.N), dtype=complex)
        for i in range(self.N-1):
            term = 1
            for j in range(self.N):
                term = kron(term, NumericalTFIM.X if j == i or j == i + 1 else NumericalTFIM.I)
            H += self.J * term
        for i in range(self.N):
            term = 1
            for j in range(self.N):
                term = kron(term, NumericalTFIM.Z if j == i else NumericalTFIM.I)
            H += self.h * term
        return H

    # Ground State and First Excited State Calculation
    def _compute_lowest_states(self):
        eigenvalues, eigenvectors = eigsh(self.H, k=2, which='SA')
        idx = np.argsort(eigenvalues)
        eigenvalues, eigenvectors = eigenvalues[idx], eigenvectors[:, idx]
        return eigenvalues[0], eigenvectors[:, 0], eigenvalues[1], eigenvectors[:, 1]

    # Density Matrix Calculation
    def _compute_density_matrix(state):
        return np.outer(state, np.conj(state))

    # Total Energy and Charge Calculation
    def _compute_gs_total_energy_and_charge(self):
        total_energy = NumericalTFIM._compute_expectation_value(self.H, self.gs0)

        Q_total = sum(
            kron(eye(2**i), kron((NumericalTFIM.I + NumericalTFIM.Z) / 2, eye(2**(self.N - i - 1))))
            for i in range(self.N)
        )

        # Compute total charge as the expectation value of the charge operator
        total_charge = NumericalTFIM._compute_expectation_value(Q_total, self.gs0)

        return total_energy, total_charge

    # Helper function to create a Pauli operator on a specific site
    def _get_pauli_operator_on_site(op_char, site_idx, N, pauli_ops):
        # pauli_ops is a dict {'I': I_op, 'X': X_op, ...}
        if not (0 <= site_idx < N):
            raise ValueError(f"Site index {site_idx} out of bounds for N={N}")
        
        op_list = [pauli_ops[op_char] if i == site_idx else pauli_ops['I'] for i in range(N)]
        
        full_operator = op_list[0]
        for i_op in range(1, N):
            full_operator = kron(full_operator, op_list[i_op], format="csc")
        return full_operator

    # Helper function for two-site operators like X_i Z_j
    def _get_two_site_operator(op1_char, site1_idx, op2_char, site2_idx, N, pauli_ops):
        if not (0 <= site1_idx < N and 0 <= site2_idx < N):
            raise ValueError(f"Site index out of bounds for N={N}")

        op1 = pauli_ops[op1_char]
        op2 = pauli_ops[op2_char]

        if site1_idx == site2_idx: 
            op_on_site = op1 @ op2 # Product on the same site
            op_list = [op_on_site if i == site1_idx else pauli_ops['I'] for i in range(N)]
        else: 
            op_list = []
            for i_op in range(N):
                if i_op == site1_idx:
                    op_list.append(op1)
                elif i_op == site2_idx:
                    op_list.append(op2)
                else:
                    op_list.append(pauli_ops['I'])
        
        full_operator = op_list[0]
        for i_op in range(1, N):
            full_operator = kron(full_operator, op_list[i_op], format="csc")
        return full_operator

    # Helper to compute expectation value <gs|Op|gs>
    def _compute_expectation_value(op_matrix, gs):
        gs_col_sparse = csc_matrix(gs.reshape(-1, 1))
        if not isinstance(op_matrix, csc_matrix):
            op_matrix = csc_matrix(op_matrix)
        val = gs_col_sparse.conj().T @ op_matrix @ gs_col_sparse
        return val[0,0].real

    # Optimal Rotation Angles for Energy and Charge
    def _compute_optimal_rotation_angles(self):
        """
        Computes optimal rotation angles for general N.
        For energy, Bob's local energy is P_B = h*Z_{N-1} + J*X_{N-2}X_{N-1}.
        For charge, Bob's local charge is Q_B = (I+Z_{N-1})/2.
        """
        pauli_ops_global = {'I': NumericalTFIM.I, 'X': NumericalTFIM.X, 'Y': NumericalTFIM.Y, 'Z': NumericalTFIM.Z}

        if self.N < 2:
            if self.N == 1 and self.J != 0:
                print(f"Warning: For N=1, Bob's energy P_B=hZ_0. JX_{self.N-2}X_{self.N-1} term is ignored. Recalculating E1,E2 for P_B=hZ_0.")
            elif self.N < 1:
                print(f"Warning: N={self.N} is not supported for these angle calculations. Returning zeros.")
                return 0.0, 0.0, 0.0, 0.0
            # For N=1, the J term is zero. Formulas for E1, E2 simplify.
            # Let's handle N=1 by effectively setting J_coupling to 0 for P_B construction.
            # Or, the calling code should be mindful. For now, we assume N>=2 for the J term.
            # If N=1, X_{N-2} is not defined. We'll proceed assuming N>=2 where X_{N-2} is distinct from X_{N-1} unless N=2.

        alice_site = utils.get_alice_qubit_idx(self.N)
        bob_site = utils.get_bob_qubit_idx(self.N)
        # bob_neighbor_site = N - 2 # Only defined if N >= 2

        # --- Theta_E1: Alice X0, Bob Y_{N-1} rot, P_B = hZ_{N-1} + JX_{N-2}X_{N-1} ---
        # Numerator for tan(2*theta_E1):
        # -h*(<X_{N-1}> + <X0 X_{N-1}>) - J*(<X_{N-2}Z_{N-1}> + <X0 X_{N-2}Z_{N-1}>)
        # Denominator for tan(2*theta_E1):
        #  h*(<Z_{N-1}> + <X0 Z_{N-1}>) + J*(<X_{N-2}X_{N-1}> + <X0 X_{N-2}X_{N-1}>)

        op_X_bob = NumericalTFIM._get_pauli_operator_on_site('X', bob_site, self.N, pauli_ops_global)
        op_Z_bob = NumericalTFIM._get_pauli_operator_on_site('Z', bob_site, self.N, pauli_ops_global)
        op_X0_Xbob = NumericalTFIM._get_two_site_operator('X', alice_site, 'X', bob_site, self.N, pauli_ops_global)
        op_X0_Zbob = NumericalTFIM._get_two_site_operator('X', alice_site, 'Z', bob_site, self.N, pauli_ops_global)
        op_X_alice = NumericalTFIM._get_pauli_operator_on_site('X', alice_site, self.N, pauli_ops_global) # For X0 terms

        # Terms for J part of P_B and P_C for E1
        if self.N >= 2:
            bob_neighbor_site = utils.get_bob_neighbor_qubit_idx(self.N)
            op_Xn2_Zn1 = NumericalTFIM._get_two_site_operator('X', bob_neighbor_site, 'Z', bob_site, self.N, pauli_ops_global)
            op_Xn2_Xn1 = NumericalTFIM._get_two_site_operator('X', bob_neighbor_site, 'X', bob_site, self.N, pauli_ops_global)
            
            # <X0 X_{N-2}Z_{N-1}>
            # If alice_site (0) is same as bob_neighbor_site (N-2), i.e. N=2
            if alice_site == bob_neighbor_site: # N=2 case
                op_X0_Xn2_Zn1 = NumericalTFIM._get_pauli_operator_on_site('Z', bob_site, self.N, pauli_ops_global) # X0*X0*ZN-1 = ZN-1
                op_X0_Xn2_Xn1 = NumericalTFIM._get_pauli_operator_on_site('X', bob_site, self.N, pauli_ops_global) # X0*X0*XN-1 = XN-1
            else: # N > 2
                op_X0_Xn2_Zn1 = op_X_alice @ op_Xn2_Zn1
                op_X0_Xn2_Xn1 = op_X_alice @ op_Xn2_Xn1

            exp_Xn2_Zn1 = NumericalTFIM._compute_expectation_value(op_Xn2_Zn1, self.gs0)
            exp_X0_Xn2_Zn1 = NumericalTFIM._compute_expectation_value(op_X0_Xn2_Zn1, self.gs0)
            exp_Xn2_Xn1 = NumericalTFIM._compute_expectation_value(op_Xn2_Xn1, self.gs0)
            exp_X0_Xn2_Xn1 = NumericalTFIM._compute_expectation_value(op_X0_Xn2_Xn1, self.gs0)
        else: # N=1, J terms are zero
            exp_Xn2_Zn1, exp_X0_Xn2_Zn1, exp_Xn2_Xn1, exp_X0_Xn2_Xn1 = 0,0,0,0


        num_E1_h_part = -self.h * (NumericalTFIM._compute_expectation_value(op_X_bob, self.gs0) + \
                                NumericalTFIM._compute_expectation_value(op_X0_Xbob, self.gs0))
        num_E1_J_part = -self.J * (exp_Xn2_Zn1 + exp_X0_Xn2_Zn1) if self.N >=2 else 0
        num_E1 = num_E1_h_part + num_E1_J_part
        
        den_E1_h_part = self.h * (NumericalTFIM._compute_expectation_value(op_Z_bob, self.gs0) + \
                                NumericalTFIM._compute_expectation_value(op_X0_Zbob, self.gs0))
        den_E1_J_part = self.J * (exp_Xn2_Xn1 + exp_X0_Xn2_Xn1) if self.N >=2 else 0
        den_E1 = den_E1_h_part + den_E1_J_part
        
        theta_E1 = 0.5 * np.arctan2(num_E1, den_E1)

        # --- Theta_E2: Alice Y0, Bob X_{N-1} rot, P_B effectively hZ_{N-1} for angle calc ---
        # tan(2*theta_E2) = ( <Y_{N-1}> + <Y0 Y_{N-1}> ) / ( <Z_{N-1}> + <Y0 Z_{N-1}> )
        # JX_{N-2}X_{N-1} part of P_B commutes with K_B=X_{N-1}, so doesn't affect angle.
        op_Y_bob = NumericalTFIM._get_pauli_operator_on_site('Y', bob_site, self.N, pauli_ops_global)
        op_Y0_Ybob = NumericalTFIM._get_two_site_operator('Y', alice_site, 'Y', bob_site, self.N, pauli_ops_global)
        op_Y0_Zbob = NumericalTFIM._get_two_site_operator('Y', alice_site, 'Z', bob_site, self.N, pauli_ops_global)

        num_E2 = NumericalTFIM._compute_expectation_value(op_Y_bob, self.gs0) + \
                NumericalTFIM._compute_expectation_value(op_Y0_Ybob, self.gs0)
        den_E2 = NumericalTFIM._compute_expectation_value(op_Z_bob, self.gs0) + \
                NumericalTFIM._compute_expectation_value(op_Y0_Zbob, self.gs0)
        # Factor h_field cancels if not zero, so not explicitly multiplied here.
        # If h_field is zero, Z_bob terms are zero, which is fine unless den_E2 becomes zero.
        theta_E2 = 0.5 * np.arctan2(num_E2, den_E2)
            
        # --- Charge Angles (Unaffected by the change in P_B for energy) ---
        # Theta_q1: Alice X0, Bob Y_{N-1} rot, measure Q_{N-1}
        # tan(2*theta_q1) = ( <X_{N-1}> + <X_0 X_{N-1}> ) / ( 1 + <X_0> + <Z_{N-1}> + <X_0 Z_{N-1}> )
        op_X_alice_val = NumericalTFIM._compute_expectation_value(op_X_alice, self.gs0)

        num_q1 = NumericalTFIM._compute_expectation_value(op_X_bob, self.gs0) + \
                NumericalTFIM._compute_expectation_value(op_X0_Xbob, self.gs0)
        den_q1 = 1.0 + op_X_alice_val + \
                NumericalTFIM._compute_expectation_value(op_Z_bob, self.gs0) + \
                NumericalTFIM._compute_expectation_value(op_X0_Zbob, self.gs0)
        theta_q1 = 0.5 * np.arctan2(num_q1, den_q1)

        # Theta_q2: Alice Y0, Bob X_{N-1} rot, measure Q_{N-1}
        # tan(2*theta_q2) = ( <Y_{N-1}> + <Y_0 Y_{N-1}> ) / ( 1 + <Y_0> + <Z_{N-1}> + <Y_0 Z_{N-1}> )
        op_Y_alice = NumericalTFIM._get_pauli_operator_on_site('Y', alice_site, self.N, pauli_ops_global)
        op_Y_alice_val = NumericalTFIM._compute_expectation_value(op_Y_alice, self.gs0)

        num_q2 = NumericalTFIM._compute_expectation_value(op_Y_bob, self.gs0) + \
                NumericalTFIM._compute_expectation_value(op_Y0_Ybob, self.gs0)
        den_q2 = 1.0 + op_Y_alice_val + \
                NumericalTFIM._compute_expectation_value(op_Z_bob, self.gs0) + \
                NumericalTFIM._compute_expectation_value(op_Y0_Zbob, self.gs0)
        theta_q2 = 0.5 * np.arctan2(num_q2, den_q2)

        return theta_E1, theta_E2, theta_q1, theta_q2

    # Bob's Energy and Charge Expectation Calculation

    def _compute_bob_gs_energy_and_charge(self):
        gs = csc_matrix(self.gs0.reshape(-1, 1))
        H_b = self.J * kron(eye(2**(self.N-1)), NumericalTFIM.X) + self.h * kron(eye(2**(self.N-1)), NumericalTFIM.Z)
        Q_b = kron(eye(2**(self.N-1)), (NumericalTFIM.I + NumericalTFIM.Z) / 2)
        energy_bob = (gs.getH() @ (H_b @ gs)).toarray().real.item()
        charge_bob = (gs.getH() @ (Q_b @ gs)).toarray().real.item()
        return energy_bob, charge_bob
