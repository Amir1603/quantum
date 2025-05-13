import numpy as np
from scipy.sparse import kron, eye, csc_matrix
from scipy.sparse.linalg import eigsh

# Pauli Matrices
I = csc_matrix(np.array([[1, 0], [0, 1]], dtype=complex))
X = csc_matrix(np.array([[0, 1], [1, 0]], dtype=complex))
Y = csc_matrix(np.array([[0, -1j], [1j, 0]], dtype=complex))
Z = csc_matrix(np.array([[1, 0], [0, -1]], dtype=complex))

# Hamiltonian Construction for TFIM

def build_tfim_hamiltonian(N, J, h):
    H = csc_matrix((2**N, 2**N), dtype=complex)
    for i in range(N-1):
        term = 1
        for j in range(N):
            term = kron(term, X if j == i or j == i + 1 else I)
        H += J * term
    for i in range(N):
        term = 1
        for j in range(N):
            term = kron(term, Z if j == i else I)
        H += h * term
    return H

# Ground State and First Excited State Calculation

def compute_lowest_states(H, num_states=2):
    eigenvalues, eigenvectors = eigsh(H, k=num_states, which='SA')
    idx = np.argsort(eigenvalues)
    eigenvalues, eigenvectors = eigenvalues[idx], eigenvectors[:, idx]
    return eigenvalues[0], eigenvectors[:, 0], eigenvalues[1], eigenvectors[:, 1]

# Density Matrix Calculation

def compute_density_matrix(state):
    return np.outer(state, np.conj(state))

# Total Energy and Charge Calculation

def compute_total_energy_and_charge(H, ground_state, N):
    gs = csc_matrix(ground_state.reshape(-1, 1))
    total_energy = (gs.getH() @ (H @ gs)).toarray().real.item()

    Q_total = sum(kron(eye(2**i), kron((I + Z)/2, eye(2**(N-i-1)))) for i in range(N))
    total_charge = (gs.getH() @ (Q_total @ gs)).toarray().real.item()

    return total_energy, total_charge

# Expectation Values Calculation

def compute_expectation_values(ground_state, N):
    gs = csc_matrix(ground_state.reshape(-1, 1))
    Z_exp = [(gs.getH() @ kron(kron(eye(2**i), Z), eye(2**(N-i-1))) @ gs).toarray().real.item() for i in range(N)]
    XX_exp = [(gs.getH() @ kron(kron(eye(2**i), kron(X, X)), eye(2**(N-i-2))) @ gs).toarray().real.item() for i in range(N-1)]
    return Z_exp, XX_exp

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
def _compute_expectation_value(op_matrix, ground_state_vector):
    gs_col_sparse = csc_matrix(ground_state_vector.reshape(-1, 1))
    if not isinstance(op_matrix, csc_matrix):
        op_matrix = csc_matrix(op_matrix)
    val = gs_col_sparse.conj().T @ op_matrix @ gs_col_sparse
    return val[0,0].real

# Optimal Rotation Angles for Energy and Charge
def compute_optimal_rotation_angles(H, ground_state, N, J_coupling, h_field):
    """
    Computes optimal rotation angles for general N.
    For energy, Bob's local energy is P_B = h*Z_{N-1} + J*X_{N-2}X_{N-1}.
    For charge, Bob's local charge is Q_B = (I+Z_{N-1})/2.
    """
    pauli_ops_global = {'I': I, 'X': X, 'Y': Y, 'Z': Z} # Use module-level I,X,Y,Z

    if N < 2:
        if N == 1 and J_coupling != 0: # Interaction term J*X_{N-2}X_{N-1} is ill-defined
             print(f"Warning: For N=1, Bob's energy P_B=hZ_0. JX_{N-2}X_{N-1} term is ignored. Recalculating E1,E2 for P_B=hZ_0.")
        elif N < 1:
             print(f"Warning: N={N} is not supported for these angle calculations. Returning zeros.")
             return 0.0, 0.0, 0.0, 0.0
        # For N=1, the J term is zero. Formulas for E1, E2 simplify.
        # Let's handle N=1 by effectively setting J_coupling to 0 for P_B construction.
        # Or, the calling code should be mindful. For now, we assume N>=2 for the J term.
        # If N=1, X_{N-2} is not defined. We'll proceed assuming N>=2 where X_{N-2} is distinct from X_{N-1} unless N=2.

    alice_site = 0
    bob_site = N - 1
    # bob_neighbor_site = N - 2 # Only defined if N >= 2

    # --- Theta_E1: Alice X0, Bob Y_{N-1} rot, P_B = hZ_{N-1} + JX_{N-2}X_{N-1} ---
    # Numerator for tan(2*theta_E1):
    # -h*(<X_{N-1}> + <X0 X_{N-1}>) - J*(<X_{N-2}Z_{N-1}> + <X0 X_{N-2}Z_{N-1}>)
    # Denominator for tan(2*theta_E1):
    #  h*(<Z_{N-1}> + <X0 Z_{N-1}>) + J*(<X_{N-2}X_{N-1}> + <X0 X_{N-2}X_{N-1}>)

    op_X_bob = _get_pauli_operator_on_site('X', bob_site, N, pauli_ops_global)
    op_Z_bob = _get_pauli_operator_on_site('Z', bob_site, N, pauli_ops_global)
    op_X0_Xbob = _get_two_site_operator('X', alice_site, 'X', bob_site, N, pauli_ops_global)
    op_X0_Zbob = _get_two_site_operator('X', alice_site, 'Z', bob_site, N, pauli_ops_global)
    op_X_alice = _get_pauli_operator_on_site('X', alice_site, N, pauli_ops_global) # For X0 terms

    # Terms for J part of P_B and P_C for E1
    if N >= 2:
        bob_neighbor_site = N - 2
        op_Xn2_Zn1 = _get_two_site_operator('X', bob_neighbor_site, 'Z', bob_site, N, pauli_ops_global)
        op_Xn2_Xn1 = _get_two_site_operator('X', bob_neighbor_site, 'X', bob_site, N, pauli_ops_global)
        
        # <X0 X_{N-2}Z_{N-1}>
        # If alice_site (0) is same as bob_neighbor_site (N-2), i.e. N=2
        if alice_site == bob_neighbor_site: # N=2 case
             op_X0_Xn2_Zn1 = _get_pauli_operator_on_site('Z', bob_site, N, pauli_ops_global) # X0*X0*ZN-1 = ZN-1
             op_X0_Xn2_Xn1 = _get_pauli_operator_on_site('X', bob_site, N, pauli_ops_global) # X0*X0*XN-1 = XN-1
        else: # N > 2
             op_X0_Xn2_Zn1 = op_X_alice @ op_Xn2_Zn1
             op_X0_Xn2_Xn1 = op_X_alice @ op_Xn2_Xn1

        exp_Xn2_Zn1 = _compute_expectation_value(op_Xn2_Zn1, ground_state)
        exp_X0_Xn2_Zn1 = _compute_expectation_value(op_X0_Xn2_Zn1, ground_state)
        exp_Xn2_Xn1 = _compute_expectation_value(op_Xn2_Xn1, ground_state)
        exp_X0_Xn2_Xn1 = _compute_expectation_value(op_X0_Xn2_Xn1, ground_state)
    else: # N=1, J terms are zero
        exp_Xn2_Zn1, exp_X0_Xn2_Zn1, exp_Xn2_Xn1, exp_X0_Xn2_Xn1 = 0,0,0,0


    num_E1_h_part = -h_field * (_compute_expectation_value(op_X_bob, ground_state) + \
                               _compute_expectation_value(op_X0_Xbob, ground_state))
    num_E1_J_part = -J_coupling * (exp_Xn2_Zn1 + exp_X0_Xn2_Zn1) if N >=2 else 0
    num_E1 = num_E1_h_part + num_E1_J_part
    
    den_E1_h_part = h_field * (_compute_expectation_value(op_Z_bob, ground_state) + \
                              _compute_expectation_value(op_X0_Zbob, ground_state))
    den_E1_J_part = J_coupling * (exp_Xn2_Xn1 + exp_X0_Xn2_Xn1) if N >=2 else 0
    den_E1 = den_E1_h_part + den_E1_J_part
    
    theta_E1 = 0.5 * np.arctan2(num_E1, den_E1)

    # --- Theta_E2: Alice Y0, Bob X_{N-1} rot, P_B effectively hZ_{N-1} for angle calc ---
    # tan(2*theta_E2) = ( <Y_{N-1}> + <Y0 Y_{N-1}> ) / ( <Z_{N-1}> + <Y0 Z_{N-1}> )
    # JX_{N-2}X_{N-1} part of P_B commutes with K_B=X_{N-1}, so doesn't affect angle.
    op_Y_bob = _get_pauli_operator_on_site('Y', bob_site, N, pauli_ops_global)
    op_Y0_Ybob = _get_two_site_operator('Y', alice_site, 'Y', bob_site, N, pauli_ops_global)
    op_Y0_Zbob = _get_two_site_operator('Y', alice_site, 'Z', bob_site, N, pauli_ops_global)

    num_E2 = _compute_expectation_value(op_Y_bob, ground_state) + \
             _compute_expectation_value(op_Y0_Ybob, ground_state)
    den_E2 = _compute_expectation_value(op_Z_bob, ground_state) + \
             _compute_expectation_value(op_Y0_Zbob, ground_state)
    # Factor h_field cancels if not zero, so not explicitly multiplied here.
    # If h_field is zero, Z_bob terms are zero, which is fine unless den_E2 becomes zero.
    theta_E2 = 0.5 * np.arctan2(num_E2, den_E2)
        
    # --- Charge Angles (Unaffected by the change in P_B for energy) ---
    # Theta_q1: Alice X0, Bob Y_{N-1} rot, measure Q_{N-1}
    # tan(2*theta_q1) = ( <X_{N-1}> + <X_0 X_{N-1}> ) / ( 1 + <X_0> + <Z_{N-1}> + <X_0 Z_{N-1}> )
    op_X_alice_val = _compute_expectation_value(op_X_alice, ground_state)

    num_q1 = _compute_expectation_value(op_X_bob, ground_state) + \
             _compute_expectation_value(op_X0_Xbob, ground_state)
    den_q1 = 1.0 + op_X_alice_val + \
             _compute_expectation_value(op_Z_bob, ground_state) + \
             _compute_expectation_value(op_X0_Zbob, ground_state)
    theta_q1 = 0.5 * np.arctan2(num_q1, den_q1)

    # Theta_q2: Alice Y0, Bob X_{N-1} rot, measure Q_{N-1}
    # tan(2*theta_q2) = ( <Y_{N-1}> + <Y_0 Y_{N-1}> ) / ( 1 + <Y_0> + <Z_{N-1}> + <Y_0 Z_{N-1}> )
    op_Y_alice = _get_pauli_operator_on_site('Y', alice_site, N, pauli_ops_global)
    op_Y_alice_val = _compute_expectation_value(op_Y_alice, ground_state)

    num_q2 = _compute_expectation_value(op_Y_bob, ground_state) + \
             _compute_expectation_value(op_Y0_Ybob, ground_state)
    den_q2 = 1.0 + op_Y_alice_val + \
             _compute_expectation_value(op_Z_bob, ground_state) + \
             _compute_expectation_value(op_Y0_Zbob, ground_state)
    theta_q2 = 0.5 * np.arctan2(num_q2, den_q2)

    return theta_E1, theta_E2, theta_q1, theta_q2

# Bob's Energy and Charge Expectation Calculation

def compute_bob_energy_and_charge(H, ground_state, N, J, h):
    gs = csc_matrix(ground_state.reshape(-1, 1))
    H_b = J * kron(eye(2**(N-1)), X) + h * kron(eye(2**(N-1)), Z)
    Q_b = kron(eye(2**(N-1)), (I + Z) / 2)
    energy_bob = (gs.getH() @ (H_b @ gs)).toarray().real.item()
    charge_bob = (gs.getH() @ (Q_b @ gs)).toarray().real.item()
    return energy_bob, charge_bob
