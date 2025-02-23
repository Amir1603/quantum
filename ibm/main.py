import argparse
from conf import Conf
from runner import Runner


def run(p_dephase, conf, runner):
    runner.initialize(p_dephase)
    runner.single_run(p_dephase, conf)


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

    runner = Runner(conf)

    if conf.p_dephase_list:
        for p_dephase in conf.p_dephase_list:
            run(p_dephase, conf, runner)
    else:
        run(None, conf, runner)