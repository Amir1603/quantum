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
    parser = argparse.ArgumentParser()

    parser.add_argument('--h-param', type=float)
    parser.add_argument('--k-param', type=float)
    parser.add_argument('--total-shots', type=float)
    parser.add_argument('--run-all-conf', action=argparse.BooleanOptionalAction)

    args = parser.parse_args()

    confs = []

    if args.run_all_conf:
        confs = Conf.generate_all_confs()
    else:
        conf = Conf()
        conf.load()

        if args.h_param:
            conf.h = args.h_param
        if args.k_param:
            conf.k = args.k_param
        if args.total_shots:
            conf.total_shots = args.total_shots

        if conf.p_dephase and conf.run_estimator:
            raise "Cannot run Estimator with dephasing noise!"

        confs.append(conf)

    print(len(confs))
    print('#########################################################')
    print()
    print(f'sim num: {len([i for i in confs if i.run_simulator])}')
    print(f'sampler sim num: {len([i for i in confs if i.run_sampler and i.p_dephase is not None])}')
    print(f'sampler num: {len([i for i in confs if i.run_sampler and i.p_dephase is None])}')
    print(f'estimator num: {len([i for i in confs if i.run_estimator])}')

    input("Press Enter to continue...")

    for c in confs:
        print()
        print('****************************************************')
        print(c)
        print('****************************************************')
        print()
        runner = Runner(c)
        single_run(c, runner, p_dephase=c.p_dephase, backend_name=c.backend)

    Runner.wrap()
