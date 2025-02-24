import argparse
from conf import Conf
from runner import Runner


def run_over_list(l, lambda_func):
    if l:
        for item in l:
            lambda_func(item)
    else:
        lambda_func(None)


def single_run(conf, runner, p_dephase=None, backend_name=None):
    runner.init_run(p_dephase, backend_name)
    runner.exec(conf)
    runner.finalize_run()


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

    run_over_list(conf.backends,
                  lambda backend:
                    run_over_list(conf.p_dephase_list,
                                  lambda p_dephase:
                                    single_run(conf, runner, p_dephase=p_dephase, backend_name=backend)))
