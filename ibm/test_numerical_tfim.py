import numpy as np
from scipy.sparse import csc_matrix

from numerical_tfim import (
    build_tfim_hamiltonian,
    compute_lowest_states,
    compute_total_energy_and_charge,
    compute_expectation_values,
    compute_optimal_rotation_angles,
    compute_bob_energy_and_charge,
    compute_density_matrix,
)

def test_build_tfim_hamiltonian():
    # Arrange
    N, J, h = 2, 1, 1

    # Act
    H = build_tfim_hamiltonian(N, J, h)

    # Assert
    assert H.shape == (4, 4), f"Expected Hamiltonian shape (4, 4), but got {H.shape}"

def test_ground_state_energy():
    # Arrange
    N, J, h = 2, 1, 1
    H = build_tfim_hamiltonian(N, J, h)
    E_analytic = -np.sqrt(4 * h**2 + J**2)

    # Act
    E_gs, _, _, _ = compute_lowest_states(H)

    # Assert
    assert np.isclose(E_gs, E_analytic), f"Ground state energy mismatch: got {E_gs}, expected {E_analytic}"

def test_total_energy_and_charge():
    # Arrange
    N, J, h = 2, 1, 1
    H = build_tfim_hamiltonian(N, J, h)
    _, gs, _, _ = compute_lowest_states(H)
    energy_analytic = -np.sqrt(4 * h**2 + J**2)
    Q_analytic = N * (0.5 - (h / np.sqrt(4 * h**2 + J**2)))

    # Act
    total_energy, total_charge = compute_total_energy_and_charge(H, gs, N)

    # Assert
    assert np.isclose(total_energy, energy_analytic), f"Total energy mismatch: got {total_energy}, expected {-np.sqrt(4 * h**2 + J**2)}"
    assert np.isclose(total_charge, Q_analytic), f"Total charge mismatch: got {total_charge}, expected {Q_analytic}"

def test_expectation_values():
    # Arrange
    N, J, h = 2, 1, 1
    H = build_tfim_hamiltonian(N, J, h)
    _, gs, _, _ = compute_lowest_states(H)

    # Act
    Z_exp, XX_exp = compute_expectation_values(gs, N)

    # Assert
    assert len(Z_exp) == N, f"Z expectation values length mismatch: got {len(Z_exp)}, expected {N}"
    assert len(XX_exp) == N - 1, f"XX expectation values length mismatch: got {len(XX_exp)}, expected {N - 1}"

def test_optimal_rotation_angles():
    # Arrange
    N, J, h = 2, 1, 1
    H = build_tfim_hamiltonian(N, J, h)
    _, gs, _, _ = compute_lowest_states(H)
    theta_E_analytic = 0.5 * np.arctan2(-2 * h, J)
    theta_q_analytic = 0.5 * np.arctan2(-J, 2 * h)

    # Act
    theta_E1, theta_E2, theta_q1, theta_q2 = compute_optimal_rotation_angles(H, gs, N, J, h)

    # Assert
    assert np.isclose(theta_E1, theta_E_analytic), f"Theta_E1 mismatch: got {theta_E1}, expected {theta_E_analytic}"
    assert np.isclose(theta_E2, -theta_E_analytic), f"Theta_E2 mismatch: got {theta_E2}, expected {-theta_E_analytic}"
    assert np.isclose(theta_q1, theta_q_analytic), f"Theta_q1 mismatch: got {theta_q1}, expected {theta_q_analytic}"
    assert np.isclose(theta_q2, -theta_q_analytic), f"Theta_q2 mismatch: got {theta_q2}, expected {-theta_q_analytic}"

def test_bob_energy_and_charge():
    # Arrange
    N, J, h = 2, 1, 1
    H = build_tfim_hamiltonian(N, J, h)
    _, gs, _, _ = compute_lowest_states(H)
    energy_bob_analytic = -h
    charge_bob_analytic = 0.5 - (h / np.sqrt(4 * h**2 + J**2))

    # Act
    energy_bob, charge_bob = compute_bob_energy_and_charge(H, gs, N, J, h)

    # Assert
    assert np.isclose(energy_bob, energy_bob_analytic), f"Bob energy mismatch: got {energy_bob}, expected {energy_bob_analytic}"
    assert np.isclose(charge_bob, charge_bob_analytic), f"Bob charge mismatch: got {charge_bob}, expected {charge_bob_analytic}"

def _get_analytical_ground_and_excited_states(J, h):
    cos_theta = -2 * h / np.sqrt(4 * h**2 + J**2)
    sin_theta = -J / np.sqrt(4 * h**2 + J**2)
    norm_factor = np.sqrt(2 + 2 * cos_theta)
    gs = (1 / norm_factor) * np.array([
        1,
        sin_theta,
        sin_theta,
        cos_theta
    ], dtype=complex)
    ex = (1 / norm_factor) * np.array([
        0,
        1 / np.sqrt(2),
        -1 / np.sqrt(2),
        0
    ], dtype=complex)

    return gs, ex

def test_lowest_states():
    # Arrange
    N, J, h = 2, 1, 1
    H = build_tfim_hamiltonian(N, J, h)
    gs_analytic, ex_analytic = _get_analytical_ground_and_excited_states(J, h)

    # Act
    _, gs, _, ex = compute_lowest_states(H)

    # Assert
    assert np.allclose(gs, gs_analytic), f"Ground state mismatch, result is {gs} expected {gs_analytic}"
    assert np.allclose(ex, ex_analytic), f"First excited state mismatch, result is {ex} expected {ex_analytic}"

def test_density_matrices():
    # Arrange
    N, J, h = 2, 1, 1
    H = build_tfim_hamiltonian(N, J, h)
    gs_analytic, ex_analytic = _get_analytical_ground_and_excited_states(J, h)
    analytic_ground_density = np.outer(gs_analytic, np.conj(gs_analytic))
    analytic_excited_density = np.outer(ex_analytic, np.conj(ex_analytic))
    _, gs, _, ex = compute_lowest_states(H)

    # Act
    ground_density = compute_density_matrix(gs)
    excited_density = compute_density_matrix(ex)

    # Assert
    assert np.allclose(ground_density, analytic_ground_density) , f"Ground density matrix mismatch, result is {ground_density} expected {analytic_ground_density}"
    assert np.allclose(excited_density, analytic_excited_density), f"Excited density matrix mismatch, result is {excited_density} expected {analytic_excited_density}"
