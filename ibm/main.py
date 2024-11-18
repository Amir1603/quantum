import argparse
import analysis
import runner
from qiskit.quantum_info import SparsePauliOp
import numpy as np

if __name__ == "__main__":
    parser = argparse.ArgumentParser(add_help=False)

    parser.add_argument('-p', '--dephase', type=float)
    parser.add_argument('-h', type=float, default=1.0)
    parser.add_argument('-k', type=float, default=1.0)
    parser.add_argument('--total-shots', type=float, default=1024)

    parser.add_argument('--run-simulator', action='store_true')
    parser.add_argument('--run-sampler', action='store_true')
    parser.add_argument('--run-estimator', action='store_true')
    parser.add_argument('--run-all', action='store_true')

    args = parser.parse_args()

    p_dephase = args.dephase
    h = args.h
    k = args.k
    total_shots = args.total_shots

    run_simulator = args.run_simulator or args.run_all
    run_sampler = args.run_sampler or args.run_all
    run_estimator = args.run_estimator or args.run_all

    if p_dephase and run_estimator:
        raise "Cannot run Estimator with dephasing noise!"

    h1 = SparsePauliOp.from_list([("ZI", h), ("II", h**2 / np.sqrt(h**2 + k**2))])
    v = SparsePauliOp.from_list([("XX", 2 * k), ("II", 2 * k**2 / np.sqrt(h**2 + k**2))])

    noise_model = runner.create_noise_model(p_dephase) if p_dephase else None
    backend, sampler, estimator = runner.initialize(noise_model)

    qc_h1, qc_h1_transpiled = runner.qet_circuit(h, k, False, h1.num_qubits, 'h1', backend)
    qc_v, qc_v_transpiled = runner.qet_circuit(h, k, True, v.num_qubits, 'v', backend)

    h1_counts_list = []
    v_counts_list = []
    legend = []
    colors = []

    if run_simulator:
        print('Running simulator')
        h1_counts_sim = runner.run_sim(qc_h1, "H1", total_shots)
        v_counts_sim = runner.run_sim(qc_v, "V", total_shots)
        
        analysis.print_expectations(h1_counts_sim, v_counts_sim, total_shots)
        h1_counts_list.append(h1_counts_sim)
        v_counts_list.append(v_counts_sim)
        legend.append('Simulator')
        colors.append('crimson')

    if run_sampler:
        print('Running sampler')

        h1_counts_hw = runner. run_sampler(sampler, qc_h1_transpiled, total_shots)
        v_counts_hw = runner.run_sampler(sampler, qc_v_transpiled, total_shots)
        
        analysis.print_expectations(h1_counts_hw, v_counts_hw, total_shots)
        h1_counts_list.append(h1_counts_hw)
        v_counts_list.append(v_counts_hw)
        legend.append('Raw Sampler')
        colors.append('midnightblue')

    if run_estimator:
        print('Running estimator')

        result_h1 = runner.run_estimator(estimator, qc_h1_transpiled, "Z", op1=h, op2=h**2 / np.sqrt(h**2 + k**2))
        result_v = runner.run_estimator(estimator, qc_v_transpiled, "XX", op1=2*k, op2=2 * k**2 / np.sqrt(h**2 + k**2))
        analysis.print_results(result_h1, result_v)

    analysis.create_histograms(h1_counts_list, v_counts_list, legend, colors, total_shots)
