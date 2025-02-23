import argparse
import runner
from qiskit.quantum_info import SparsePauliOp
import numpy as np


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument('-p', '--dephase', nargs='+', type=float)
    parser.add_argument('--h-param', type=float, default=1.0)
    parser.add_argument('--k-param', type=float, default=1.0)
    parser.add_argument('--total-shots', type=float, default=1024)
    parser.add_argument('--error_mitigation', action='store_true')

    parser.add_argument('--run-simulator', action='store_true')
    parser.add_argument('--run-sampler', action='store_true')
    parser.add_argument('--run-estimator', action='store_true')
    parser.add_argument('--run-all', action='store_true')

    args = parser.parse_args()

    p_dephase_list = args.dephase
    h = args.h_param
    k = args.k_param
    total_shots = args.total_shots
    error_mitigation = args.error_mitigation

    run_simulator = args.run_simulator or args.run_all
    run_sampler = args.run_sampler or args.run_all
    run_estimator = args.run_estimator or args.run_all

    if p_dephase_list and run_estimator:
        raise "Cannot run Estimator with dephasing noise!"

    h1 = SparsePauliOp.from_list([("ZI", h), ("II", h**2 / np.sqrt(h**2 + k**2))])
    v = SparsePauliOp.from_list([("XX", 2 * k), ("II", 2 * k**2 / np.sqrt(h**2 + k**2))])

    p_dephase_list.sort()
    for p_dephase in p_dephase_list:
        runner.single_run(h, k, total_shots, h1, v, p_dephase, run_simulator, run_sampler, run_estimator, error_mitigation)