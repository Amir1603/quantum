import argparse
import runner


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

    run = runner.Runner(h, k, total_shots)
    p_dephase_list.sort()

    for p_dephase in p_dephase_list:
        run.initialize(p_dephase)
        runner.single_run(p_dephase, run_simulator, run_sampler, run_estimator, error_mitigation)