import numpy as np
from .analytical_tfim import MyCalculatorTFIM
from .numerical_tfim import NumericalTFIM
import pytest

@pytest.fixture
def ntfim():
    """
    Fixture to create a NumericalTFIM instance for testing.
    """
    N = 2
    J = 1.0
    h = 1.0
    ntfim = NumericalTFIM(N, J, h)

    ntfim.calc_all()

    return ntfim

@pytest.fixture
def atfim():
    """
    Fixture to create an AnalyticalTFIM instance for testing.
    """
    N = 2
    J = 1.0
    h = 1.0

    class Conf:
        def __init__(self):
            self.p_depol_error = 0.0
            self.p_bitflip_error = 0.0
            self.p_alice_phaseflip_error = 0.0
            self.p_bob_phaseflip_error = 0.0
            self.p_excited_mixture = 0.0
            self.p_excited_superposition_error = 0.0

    conf = Conf()
    atfim = MyCalculatorTFIM(N, J, h, conf)

    atfim.calc_all()

    return atfim

@pytest.mark.parametrize("name", ["ntfim"])
def test_build_tfim_hamiltonian(request, name):
    tfim = request.getfixturevalue(name)
    # Assert
    assert tfim.H.shape == (4, 4), f"Expected Hamiltonian shape (4, 4), but got {tfim.H.shape}"

@pytest.mark.parametrize("name", ["ntfim"])
def test_ground_state_energy(request, name):
    tfim = request.getfixturevalue(name)
    # Arrange
    E_analytic = -np.sqrt(4 * tfim.h**2 + tfim.J**2)

    # Assert
    assert np.isclose(tfim.E0, E_analytic), f"Ground state energy mismatch: got {tfim.E0}, expected {E_analytic}"

@pytest.mark.parametrize("name", ["ntfim"])
def test_total_energy_and_charge(request, name):
    tfim = request.getfixturevalue(name)
    # Arrange
    energy_analytic = -np.sqrt(4 * tfim.h**2 + tfim.J**2)
    Q_analytic = tfim.N * (0.5 - (tfim.h / np.sqrt(4 * tfim.h**2 + tfim.J**2)))

    # Assert
    assert np.isclose(tfim.total_energy, energy_analytic), f"Total energy mismatch: got {tfim.total_energy}, expected {energy_analytic}"
    assert np.isclose(tfim.total_charge, Q_analytic), f"Total charge mismatch: got {tfim.total_charge}, expected {Q_analytic}"

@pytest.mark.parametrize("name", ["ntfim", "atfim"])
def test_optimal_rotation_angles(request, name):
    """
    Tests compute_optimal_rotation_angles for N=2 against derived analytical expressions.
    """
    tfim = request.getfixturevalue(name)
    # Analytical calculations for N=2
    # E_gs_analytic for pure analytical check, can also use E_gs_numerical if confident in it
    E_gs_analytic = -np.sqrt(4 * tfim.h**2 + tfim.J**2)
    
    # Assert that the numerically found ground state energy is correct (optional, good check)
    assert np.isclose(tfim.total_energy, E_gs_analytic), \
        f"Ground state energy mismatch: Num={tfim.total_energy}, Ana={E_gs_analytic}"

    analytic_theta_E1 = 0.5 * np.arctan2(3 * tfim.h * tfim.J, 
                                     -(2 * tfim.h**2 + tfim.J**2))

    # Theta_E2: tan(2*theta) = -J / (2*h)
    if tfim.h == 0:
        if tfim.J == 0:
            analytic_theta_E2 = 0.0
        else: # Denominator is effectively zero (as <Z1> might be zero if h=0)
              # Numerator is J. tan is J/0 -> infinite
            analytic_theta_E2 = 0.5 * (np.pi / 2.0) if tfim.J > 0 else 0.5 * (-np.pi / 2.0)
    else: # h != 0
        analytic_theta_E2 = 0.5 * np.arctan2(tfim.J, -2 * tfim.h)


    # Theta_q1: tan(2*theta) = -J / (E_gs + 2h)
    denominator_q1 = E_gs_analytic + 2 * tfim.h
    if np.isclose(denominator_q1, 0):
        if np.isclose(-tfim.J, 0): # 0/0 case
            analytic_theta_q1 = 0.0
        else: # +/- inf case
            analytic_theta_q1 = 0.5 * (np.pi / 2) if -tfim.J > 0 else 0.5 * (-np.pi/2)
    else:
        analytic_theta_q1 = 0.5 * np.arctan(tfim.J/denominator_q1)

    # Theta_q2: tan(2*theta) = J / (E_gs + 2h)
    denominator_q2 = E_gs_analytic + 2 * tfim.h
    if np.isclose(denominator_q2, 0):
        if np.isclose(tfim.J, 0): # 0/0 case
            analytic_theta_q2 = 0.0
        else: # +/- inf case
            analytic_theta_q2 = 0.5 * (np.pi / 2) if tfim.J > 0 else 0.5 * (-np.pi/2)
    else:
        analytic_theta_q2 = 0.5 * np.arctan(-tfim.J/denominator_q2)

    # Assertions
    # Using a tolerance, e.g., atol=1e-9
    assert np.isclose(tfim.theta_E1, analytic_theta_E1, atol=1e-9), \
        f"Theta_E1 mismatch: Num={tfim.theta_E1:.7f}, Ana={analytic_theta_E1:.7f}"
    assert np.isclose(tfim.theta_E2, analytic_theta_E2, atol=1e-9), \
        f"Theta_E2 mismatch: Num={tfim.theta_E2:.7f}, Ana={analytic_theta_E2:.7f}"
    assert np.isclose(tfim.theta_q1, analytic_theta_q1, atol=1e-9), \
        f"Theta_q1 mismatch: Num={tfim.theta_q1:.7f}, Ana={analytic_theta_q1:.7f}"
    assert np.isclose(tfim.theta_q2, analytic_theta_q2, atol=1e-9), \
        f"Theta_q2 mismatch: Num={tfim.theta_q2:.7f}, Ana={analytic_theta_q2:.7f}"

@pytest.mark.parametrize("name", ["ntfim", "atfim"])
def test_bob_energy_and_charge(request, name):
    tfim = request.getfixturevalue(name)
    # Arrange
    energy_bob_analytic = -(2 * tfim.h**2 + tfim.J**2) / np.sqrt(4 * tfim.h**2 + tfim.J**2)
    charge_bob_analytic = 0.5 - (tfim.h / np.sqrt(4 * tfim.h**2 + tfim.J**2))

    # Assert
    assert np.isclose(tfim.bob_energy, energy_bob_analytic), f"Bob energy mismatch: got {tfim.bob_energy}, expected {energy_bob_analytic}"
    assert np.isclose(tfim.bob_charge, charge_bob_analytic), f"Bob charge mismatch: got {tfim.bob_charge}, expected {charge_bob_analytic}"

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

@pytest.mark.parametrize("name", ["ntfim", "atfim"])
def test_lowest_states(request, name):
    tfim = request.getfixturevalue(name)
    # Arrange
    gs_analytic, ex_analytic = _get_n2_analytical_ground_and_excited_states(tfim.J, tfim.h)

    # Assert
    # Phase alignment for ground state
    # Find first significant component in gs_analytic to use as phase reference
    ref_idx_gs_analytic = int(np.argmax(np.abs(gs_analytic)))
    if np.abs(gs_analytic[ref_idx_gs_analytic]) > 1e-9: # Avoid division by zero
        # Phase factor to make gs_analytic[ref_idx] have the same phase as gs[ref_idx]
        phase_factor_gs = (tfim.gs0[ref_idx_gs_analytic] * np.conj(gs_analytic[ref_idx_gs_analytic]))
        if np.abs(phase_factor_gs) > 1e-9:
            phase_correction_gs = phase_factor_gs / np.abs(phase_factor_gs)
        else:
            phase_correction_gs = 1.0 # No change if product is zero
        gs_analytic_aligned = gs_analytic * phase_correction_gs
    else: # gs_analytic is (close to) zero vector
        gs_analytic_aligned = gs_analytic.copy()

    assert np.allclose(tfim.gs0, gs_analytic_aligned, atol=1e-7), \
        f"Ground state mismatch:\nNum: {tfim.gs0}\nAna_orig: {gs_analytic}\nAna_aligned: {gs_analytic_aligned}"

    # Phase alignment for first excited state
    ref_idx_ex_analytic = int(np.argmax(np.abs(ex_analytic)))
    if np.abs(ex_analytic[ref_idx_ex_analytic]) > 1e-9:
        phase_factor_ex = (tfim.ex1[ref_idx_ex_analytic] * np.conj(ex_analytic[ref_idx_ex_analytic]))
        if np.abs(phase_factor_ex) > 1e-9:
            phase_correction_ex = phase_factor_ex / np.abs(phase_factor_ex)
        else:
            phase_correction_ex = 1.0
        ex_analytic_aligned = ex_analytic * phase_correction_ex
    else:
        ex_analytic_aligned = ex_analytic.copy()

    assert np.allclose(tfim.ex1, ex_analytic_aligned, atol=1e-7), \
        f"Excited state mismatch:\nNum: {tfim.ex1}\nAna_orig: {ex_analytic}\nAna_aligned: {ex_analytic_aligned}"

@pytest.mark.parametrize("name", ["ntfim", "atfim"])
def test_density_matrices(request, name):
    tfim = request.getfixturevalue(name)
    # Arrange
    gs_analytic, ex_analytic = _get_n2_analytical_ground_and_excited_states(tfim.J, tfim.h)
    analytic_ground_density = np.outer(gs_analytic, np.conj(gs_analytic))
    analytic_excited_density = np.outer(ex_analytic, np.conj(ex_analytic))

    # Assert
    assert np.allclose(tfim.gs_rho, analytic_ground_density) , f"Ground density matrix mismatch, result is {tfim.gs_rho} expected {analytic_ground_density}"
    assert np.allclose(tfim.ex1_rho, analytic_excited_density), f"Excited density matrix mismatch, result is {tfim.ex1_rho} expected {analytic_excited_density}"
