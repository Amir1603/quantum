import argparse
from conf import Conf
import runner


if __name__ == "__main__":

    conf = Conf()

    parser = argparse.ArgumentParser()

    parser.add_argument('-p', '--dephase', nargs='+', type=float)
    parser.add_argument('--h-param', type=float)
    parser.add_argument('--k-param', type=float)
    parser.add_argument('--total-shots', type=float)

    args = parser.parse_args()

    if args.dephase:
        conf.p_dephase_list = args.dephase
    if args.h_param:
        conf.h = args.h_param
    if args.k_param:
        conf.k = args.k_param
    if args.total_shots:
        conf.total_shots = args.total_shots

    conf.p_dephase_list.sort()

    if conf.p_dephase_list and conf.run_estimator:
        raise "Cannot run Estimator with dephasing noise!"

    run = runner.Runner(conf)

    for p_dephase in conf.p_dephase_list:
        run.initialize(p_dephase)
        run.single_run(p_dephase, conf)