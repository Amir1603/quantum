import runner
from qiskit.quantum_info import SparsePauliOp
import numpy as np

h = 1.0
k = 1.0

total_shots = 2 ** 10

h1 = SparsePauliOp.from_list([("ZI", h), ("II", h**2 / np.sqrt(h**2 + k**2))])
v = SparsePauliOp.from_list([("XX", 2 * k), ("II", 2 * k**2 / np.sqrt(h**2 + k**2))])

backend, sampler, estimator = runner.initialize()

qc_h1, qc_h1_transpiled = runner.qet_circuit(h, k, False, h1.num_qubits, 'h1', backend)
qc_v, qc_v_transpiled = runner.qet_circuit(h, k, True, v.num_qubits, 'v', backend)

h1_counts_sim = runner.run_sim(qc_h1, "H1", total_shots)
v_counts_sim = runner.run_sim(qc_v, "V", total_shots)

h1_counts_hw = runner. run_sampler(sampler, qc_h1_transpiled, h1, total_shots)
v_counts_hw = runner.run_sampler(sampler, qc_v_transpiled, v, total_shots)

result_h1 = runner.run_estimator(estimator, qc_h1_transpiled, "Z", op1=h, op2=h**2 / np.sqrt(h**2 + k**2))
result_v = runner.run_estimator(estimator, qc_v_transpiled, "XX", op1=2*k, op2=2 * k**2 / np.sqrt(h**2 + k**2))


if __name__ == "__main__":
    pass