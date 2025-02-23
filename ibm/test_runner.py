import pytest
from unittest.mock import patch, MagicMock
from qiskit import QuantumCircuit
from qiskit.quantum_info import DensityMatrix
from runner import Runner
from conf import Conf


@pytest.fixture
def conf():
    return Conf()

@pytest.fixture
def runner(conf):
    return Runner(conf)

@patch('runner.Aer.get_backend')
@patch('runner.transpile')
@patch('runner.AerSimulator')
def test_run_sim(mock_aer_simulator, mock_transpile, mock_get_backend, runner):
    mock_backend = MagicMock()
    mock_get_backend.return_value = mock_backend
    mock_job = MagicMock()
    mock_backend.run.return_value = mock_job
    mock_result = MagicMock()
    mock_job.result.return_value = mock_result
    mock_result.data.return_value = {'density_matrix': DensityMatrix.from_label('00')}
    mock_result.get_counts.return_value = {'00 00': 1024}

    qc = QuantumCircuit(2)
    counts, rho = runner._run_sim(qc, "Test")

    assert counts == {'00 00': 1024}
    assert isinstance(rho, DensityMatrix)

@patch('runner.BackendSamplerV2')
def test_run_sampler(mock_backend_sampler, runner):
    mock_sampler = MagicMock()
    mock_backend_sampler.return_value = mock_sampler
    mock_job = MagicMock()
    mock_sampler.run.return_value = mock_job
    mock_result = MagicMock()
    mock_job.result.return_value = mock_result
    mock_result._pub_results = [MagicMock()]
    mock_result._pub_results[0].data.c.get_counts.return_value = {'00': 512, '11': 512}

    qc_transpiled = QuantumCircuit(2)
    counts, rho = runner._run_sampler(qc_transpiled)

    assert counts == {'00': 512, '11': 512}
    assert isinstance(rho, DensityMatrix)

@patch('runner.BackendEstimatorV2')
def test_run_estimator(mock_backend_estimator, runner):
    mock_estimator = MagicMock()
    mock_backend_estimator.return_value = mock_estimator
    mock_job = MagicMock()
    mock_estimator.run.return_value = mock_job
    mock_result = MagicMock()
    mock_job.result.return_value = mock_result

    qc_transpiled = QuantumCircuit(2)
    result = runner._run_estimator(qc_transpiled, "Z", runner.conf, runner.conf**2 / (runner.conf**2 + runner.k**2)**0.5)

    assert result == mock_result

def test_initialize(runner):
    runner.initialize(p_dephase=0.1)
    assert runner.backend is not None
    assert runner.sampler is not None
    if runner.noise_model:
        assert runner.estimator is None
    else:
        assert runner.estimator is not None

def test_prep_error_mitigation(runner):
    runner.estimator = MagicMock()
    runner._prep_error_mitigation()
    assert runner.estimator.options.resilience.zne_mitigation
    assert runner.estimator.options.resilience.zne.amplifier == "pea"

if __name__ == '__main__':
    pytest.main()