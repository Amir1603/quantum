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

# Optimal Rotation Angles for Energy and Charge

def compute_optimal_rotation_angles(H, ground_state, N, J, h):
    gs = csc_matrix(ground_state.reshape(-1, 1))

    # Energy rotation angles (Alice Basis 1 and 2)
    H_A = h * kron(Z, eye(2**(N-1)))
    H_B = J * kron(X, eye(2**(N-1))) + h * kron(eye(2**(N-1)), Z)

    eta_E1 = (gs.getH() @ (H_B @ gs)).toarray().real.item()
    xi_E1 = (gs.getH() @ (H_A @ gs)).toarray().real.item()
    theta_E1 = 0.5 * np.arctan2(eta_E1, xi_E1)

    eta_E2 = (gs.getH() @ (H_B @ gs)).toarray().real.item()
    xi_E2 = (gs.getH() @ (H_A @ gs)).toarray().real.item()
    theta_E2 = -0.5 * np.arctan2(eta_E2, xi_E2)

    # Charge rotation angles (Alice Basis 1 and 2)
    Q_B = kron(eye(2**(N-1)), (I + Z) / 2)
    eta_q1 = (gs.getH() @ (Q_B @ gs)).toarray().real.item()
    xi_q1 = (gs.getH() @ (H_A @ gs)).toarray().real.item()
    theta_q1 = 0.5 * np.arctan2(eta_q1, xi_q1)

    eta_q2 = (gs.getH() @ (Q_B @ gs)).toarray().real.item()
    xi_q2 = (gs.getH() @ (H_A @ gs)).toarray().real.item()
    theta_q2 = -0.5 * np.arctan2(eta_q2, xi_q2)

    return theta_E1, theta_E2, theta_q1, theta_q2

# Bob's Energy and Charge Expectation Calculation

def compute_bob_energy_and_charge(H, ground_state, N, J, h):
    gs = csc_matrix(ground_state.reshape(-1, 1))
    H_b = J * kron(eye(2**(N-1)), X) + h * kron(eye(2**(N-1)), Z)
    Q_b = kron(eye(2**(N-1)), (I + Z) / 2)
    energy_bob = (gs.getH() @ (H_b @ gs)).toarray().real.item()
    charge_bob = (gs.getH() @ (Q_b @ gs)).toarray().real.item()
    return energy_bob, charge_bob
