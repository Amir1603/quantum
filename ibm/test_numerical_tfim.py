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

def test_optimal_rotation_angles_N2():
    """
    Tests compute_optimal_rotation_angles for N=2 against derived analytical expressions.
    """
    # Import necessary functions here if they are not module-level in the test file

    N, J, h = 2, 1, 1

    H_matrix = build_tfim_hamiltonian(N, J, h)
    # For N=2, eigsh might return eigenvalues in a different order than expected for gs
    # compute_lowest_states should already sort them.
    E_gs_numerical, gs_vector, _, _ = compute_lowest_states(H_matrix, num_states=2)

    # Call the function under test
    theta_E1_num, theta_E2_num, theta_q1_num, theta_q2_num = \
        compute_optimal_rotation_angles(H_matrix, gs_vector, N, J, h)

    # Analytical calculations for N=2
    # E_gs_analytic for pure analytical check, can also use E_gs_numerical if confident in it
    E_gs_analytic = -np.sqrt(4 * h**2 + J**2)
    
    # Assert that the numerically found ground state energy is correct (optional, good check)
    assert np.isclose(E_gs_numerical, E_gs_analytic), \
        f"Ground state energy mismatch: Num={E_gs_numerical}, Ana={E_gs_analytic}"

    analytic_theta_E1 = 0.5 * np.arctan2(3 * h * J, 
                                     -(2 * h**2 + J**2))

    # Theta_E2: tan(2*theta) = -J / (2*h)
    if h == 0:
        if J == 0:
            analytic_theta_E2 = 0.0
        else: # Denominator is effectively zero (as <Z1> might be zero if h=0)
              # Numerator is J. tan is J/0 -> infinite
            analytic_theta_E2 = 0.5 * (np.pi / 2.0) if J > 0 else 0.5 * (-np.pi / 2.0)
    else: # h != 0
        analytic_theta_E2 = 0.5 * np.arctan2(J, -2 * h)


    # Theta_q1: tan(2*theta) = -J / (E_gs + 2h)
    denominator_q1 = E_gs_analytic + 2 * h
    if np.isclose(denominator_q1, 0):
        if np.isclose(-J, 0): # 0/0 case
            analytic_theta_q1 = 0.0
        else: # +/- inf case
            analytic_theta_q1 = 0.5 * (np.pi / 2) if -J > 0 else 0.5 * (-np.pi/2)
    else:
        analytic_theta_q1 = 0.5 * np.arctan(J/denominator_q1)

    # Theta_q2: tan(2*theta) = J / (E_gs + 2h)
    denominator_q2 = E_gs_analytic + 2 * h
    if np.isclose(denominator_q2, 0):
        if np.isclose(J, 0): # 0/0 case
            analytic_theta_q2 = 0.0
        else: # +/- inf case
            analytic_theta_q2 = 0.5 * (np.pi / 2) if J > 0 else 0.5 * (-np.pi/2)
    else:
        analytic_theta_q2 = 0.5 * np.arctan(-J/denominator_q2)

    # Assertions
    # Using a tolerance, e.g., atol=1e-9
    assert np.isclose(theta_E1_num, analytic_theta_E1, atol=1e-9), \
        f"Theta_E1 mismatch: Num={theta_E1_num:.7f}, Ana={analytic_theta_E1:.7f}"
    assert np.isclose(theta_E2_num, analytic_theta_E2, atol=1e-9), \
        f"Theta_E2 mismatch: Num={theta_E2_num:.7f}, Ana={analytic_theta_E2:.7f}"
    assert np.isclose(theta_q1_num, analytic_theta_q1, atol=1e-9), \
        f"Theta_q1 mismatch: Num={theta_q1_num:.7f}, Ana={analytic_theta_q1:.7f}"
    assert np.isclose(theta_q2_num, analytic_theta_q2, atol=1e-9), \
        f"Theta_q2 mismatch: Num={theta_q2_num:.7f}, Ana={analytic_theta_q2:.7f}"

def test_bob_energy_and_charge():
    # Arrange
    N, J, h = 2, 1, 1
    H = build_tfim_hamiltonian(N, J, h)
    _, gs, _, _ = compute_lowest_states(H)
    energy_bob_analytic = -2 * h**2 / np.sqrt(4 * h**2 + J**2)
    charge_bob_analytic = 0.5 - (h / np.sqrt(4 * h**2 + J**2))

    # Act
    energy_bob, charge_bob = compute_bob_energy_and_charge(H, gs, N, J, h)

    # Assert
    assert np.isclose(energy_bob, energy_bob_analytic), f"Bob energy mismatch: got {energy_bob}, expected {energy_bob_analytic}"
    assert np.isclose(charge_bob, charge_bob_analytic), f"Bob charge mismatch: got {charge_bob}, expected {charge_bob_analytic}"

def _get_n2_analytical_ground_and_excited_states(J, h):
    E_gs_val = np.sqrt(4 * h**2 + J**2)

    alpha_numerator = (2 * h - E_gs_val)
    beta_numerator = J

    norm_factor_gs_sq = alpha_numerator**2 + beta_numerator**2
    norm_factor_gs = np.sqrt(norm_factor_gs_sq)

    alpha = alpha_numerator / norm_factor_gs
    beta = beta_numerator / norm_factor_gs

    gs = np.array([alpha, 0, 0, beta], dtype=complex)
    ex = (1 / np.sqrt(2)) * np.array([0, 1, -1, 0], dtype=complex)

    return gs, ex

def test_lowest_states():
    # Arrange
    N, J, h = 2, 1, 1
    H = build_tfim_hamiltonian(N, J, h)
    gs_analytic, ex_analytic = _get_n2_analytical_ground_and_excited_states(J, h)

    # Act
    _, gs, _, ex = compute_lowest_states(H)

    # Assert
    # Phase alignment for ground state
    # Find first significant component in gs_analytic to use as phase reference
    ref_idx_gs_analytic = np.argmax(np.abs(gs_analytic))
    if np.abs(gs_analytic[ref_idx_gs_analytic]) > 1e-9: # Avoid division by zero
        # Phase factor to make gs_analytic[ref_idx] have the same phase as gs[ref_idx]
        phase_factor_gs = (gs[ref_idx_gs_analytic] * np.conj(gs_analytic[ref_idx_gs_analytic]))
        if np.abs(phase_factor_gs) > 1e-9:
            phase_correction_gs = phase_factor_gs / np.abs(phase_factor_gs)
        else:
            phase_correction_gs = 1.0 # No change if product is zero
        gs_analytic_aligned = gs_analytic * phase_correction_gs
    else: # gs_analytic is (close to) zero vector
        gs_analytic_aligned = gs_analytic.copy()

    assert np.allclose(gs, gs_analytic_aligned, atol=1e-7), \
        f"Ground state mismatch:\nNum: {gs}\nAna_orig: {gs_analytic}\nAna_aligned: {gs_analytic_aligned}"

    # Phase alignment for first excited state
    ref_idx_ex_analytic = np.argmax(np.abs(ex_analytic))
    if np.abs(ex_analytic[ref_idx_ex_analytic]) > 1e-9:
        phase_factor_ex = (ex[ref_idx_ex_analytic] * np.conj(ex_analytic[ref_idx_ex_analytic]))
        if np.abs(phase_factor_ex) > 1e-9:
            phase_correction_ex = phase_factor_ex / np.abs(phase_factor_ex)
        else:
            phase_correction_ex = 1.0
        ex_analytic_aligned = ex_analytic * phase_correction_ex
    else:
        ex_analytic_aligned = ex_analytic.copy()

    assert np.allclose(ex, ex_analytic_aligned, atol=1e-7), \
        f"Excited state mismatch:\nNum: {ex}\nAna_orig: {ex_analytic}\nAna_aligned: {ex_analytic_aligned}"

def test_density_matrices():
    # Arrange
    N, J, h = 2, 1, 1
    H = build_tfim_hamiltonian(N, J, h)
    gs_analytic, ex_analytic = _get_n2_analytical_ground_and_excited_states(J, h)
    analytic_ground_density = np.outer(gs_analytic, np.conj(gs_analytic))
    analytic_excited_density = np.outer(ex_analytic, np.conj(ex_analytic))
    _, gs, _, ex = compute_lowest_states(H)

    # Act
    ground_density = compute_density_matrix(gs)
    excited_density = compute_density_matrix(ex)

    # Assert
    assert np.allclose(ground_density, analytic_ground_density) , f"Ground density matrix mismatch, result is {ground_density} expected {analytic_ground_density}"
    assert np.allclose(excited_density, analytic_excited_density), f"Excited density matrix mismatch, result is {excited_density} expected {analytic_excited_density}"
