import unittest
from unittest.mock import patch, MagicMock
from qiskit import QuantumCircuit
from qiskit.quantum_info import DensityMatrix
from ibm.runner import Runner

class TestRunner(unittest.TestCase):

    def setUp(self):
        self.h = 1.0
        self.k = 1.0
        self.total_shots = 1024
        self.runner = Runner(self.h, self.k, self.total_shots)

    @patch('ibm.runner.Aer.get_backend')
    @patch('ibm.runner.transpile')
    @patch('ibm.runner.AerSimulator')
    def test_run_sim(self, mock_aer_simulator, mock_transpile, mock_get_backend):
        mock_backend = MagicMock()
        mock_get_backend.return_value = mock_backend
        mock_job = MagicMock()
        mock_backend.run.return_value = mock_job
        mock_result = MagicMock()
        mock_job.result.return_value = mock_result
        mock_result.data.return_value = {'density_matrix': DensityMatrix.from_label('00')}
        mock_result.get_counts.return_value = {'00 00': 1024}

        qc = QuantumCircuit(2)
        counts, rho = self.runner._run_sim(qc, "Test")

        self.assertEqual(counts, {'00': 1024})
        self.assertTrue(isinstance(rho, DensityMatrix))

    @patch('ibm.runner.BackendSamplerV2')
    def test_run_sampler(self, mock_backend_sampler):
        mock_sampler = MagicMock()
        mock_backend_sampler.return_value = mock_sampler
        mock_job = MagicMock()
        mock_sampler.run.return_value = mock_job
        mock_result = MagicMock()
        mock_job.result.return_value = mock_result
        mock_result._pub_results = [MagicMock()]
        mock_result._pub_results[0].data.c.get_counts.return_value = {'00': 512, '11': 512}

        qc_transpiled = QuantumCircuit(2)
        counts, rho = self.runner._run_sampler(qc_transpiled)

        self.assertEqual(counts, {'00': 512, '11': 512})
        self.assertTrue(isinstance(rho, DensityMatrix))

    @patch('ibm.runner.BackendEstimatorV2')
    def test_run_estimator(self, mock_backend_estimator):
        mock_estimator = MagicMock()
        mock_backend_estimator.return_value = mock_estimator
        mock_job = MagicMock()
        mock_estimator.run.return_value = mock_job
        mock_result = MagicMock()
        mock_job.result.return_value = mock_result

        qc_transpiled = QuantumCircuit(2)
        result = self.runner._run_estimator(qc_transpiled, "Z", self.h, self.h**2 / (self.h**2 + self.k**2)**0.5)

        self.assertEqual(result, mock_result)

    def test_initialize(self):
        self.runner.initialize(p_dephase=0.1)
        self.assertIsNotNone(self.runner.backend)
        self.assertIsNotNone(self.runner.sampler)
        if self.runner.noise_model:
            self.assertIsNone(self.runner.estimator)
        else:
            self.assertIsNotNone(self.runner.estimator)

    def test_prep_error_mitigation(self):
        self.runner.estimator = MagicMock()
        self.runner._prep_error_mitigation()
        self.assertTrue(self.runner.estimator.options.resilience.zne_mitigation)
        self.assertEqual(self.runner.estimator.options.resilience.zne.amplifier, "pea")

if __name__ == '__main__':
    unittest.main()