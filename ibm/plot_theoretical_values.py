import matplotlib.pyplot as plt
import numpy as np
from Calculators import NumericalTFIM
import utils
from conf import Conf
from numerical_run_conf import RunConf, NumericalRunConf
from plot_utils import PlotProperties

def single_run(conf: Conf, alice_base: utils.AliceBase, hamiltonian_class: type, OB_types: dict[str, type]):
    OBs = {k: OB_class(conf.h, conf.J, conf.N, alice_base) for k, OB_class in OB_types.items()}
    H = hamiltonian_class(conf.h, conf.J, conf.N)

    ntfim = NumericalTFIM(H, list(OBs.values()))
    ntfim.calc_all(conf)

    return OBs

def run_Js(rc: RunConf):
    confs = Conf.generate_J_for_h(Conf(rc.N), 100)
    Js = [c.J for c in confs]
    ys = {}

    print(f"Running all Js ({len(Js)})")

    for c in confs:
        OBs = single_run(c, rc.alice_basis, rc.H_type, rc.OB_types)

        for name, v in OBs.items():
            if name not in ys:
                ys[name] = {False: [], True: []}

            ys[name][False].append(v.teleported_values[False])
            ys[name][True].append(v.teleported_values[True])

    for name, y_vals in ys.items():
        rc.J_pps[name].update_x("J", np.array(Js))

        a0_vals = np.array(y_vals[False])
        a1_vals = np.array(y_vals[True])

        rc.J_pps[name].update_ys(name, f"a=0", np.array(a0_vals))
        rc.J_pps[name].update_ys(name, f"a=1", np.array(a1_vals))

def run_hs(rc: RunConf):
    confs = Conf.generate_h_for_J(Conf(rc.N), 100)
    hs = [c.h for c in confs]
    ys = {}

    print(f"Running all hs ({len(hs)})")

    for c in confs:
        OBs = single_run(c, rc.alice_basis, rc.H_type, rc.OB_types)

        for name, v in OBs.items():
            if name not in ys:
                ys[name] = {False: [], True: []}

            ys[name][False].append(v.teleported_values[False])
            ys[name][True].append(v.teleported_values[True])

    for name, y_vals in ys.items():
        rc.h_pps[name].update_x("h", np.array(hs))

        a0_vals = np.array(y_vals[False])
        a1_vals = np.array(y_vals[True])

        rc.h_pps[name].update_ys(name, f"a=0", a0_vals)
        rc.h_pps[name].update_ys(name, f"a=1", a1_vals)

def run_single_error(errs, conf: Conf, rc: RunConf, err_name: str, add_N: bool = True):
    confs = [c for c in Conf.generate_from_errors(conf, errs)]
    p_errs = [err_conf.__dict__[err_name] for err_conf in errs]
    ys = {}

    print(f"Running {err_name} for J={conf.J}")

    for c in confs:
        OBs = single_run(c, rc.alice_basis, rc.H_type, rc.OB_types)

        for name, v in OBs.items():
            if name not in ys:
                ys[name] = []

            ys[name].append(v.teleported_values[False])

    for name, y_vals in ys.items():
        rc.errs_pps[name][err_name].update_x(err_name, np.array(p_errs))
        rc.errs_pps[name][err_name].update_ys(name, f"J={conf.J}", np.array(y_vals), y_lim=NumericalRunConf.get_ylim(err_name, rc.H_type))

def run_errors(rc: RunConf):
    Js = np.linspace(1.0, 4.0, 7).tolist()
    print("Running all errors")

    for err_name in NumericalRunConf.get_errors():
        conf = Conf(rc.N)
        errs = NumericalRunConf.generate_errors_configurations(err_name)

        for J in Js:
            conf.J = J
            run_single_error(errs, conf, rc, err_name)

if __name__ == "__main__":
    plt.autoscale(enable=True, axis='both', tight=None)
    run_confs = [NumericalRunConf.AliceConf(), NumericalRunConf.NNConf()]
    pps = []

    for run_conf in run_confs:
        class_comm_vs_N_pps = {}
        combined_alice_base_J_pps = {}
        combined_alice_base_h_pps = {}

        for rc in run_conf.confs:
            print(f"Calculating theoretical values for {rc.name} with AliceBase={rc.alice_basis} and N={rc.N}...")

            run_Js(rc)
            run_hs(rc)
            run_errors(rc)

            # Get list with all PlotProperties objects
            # No PlotProperties for class_comm_err vs N and for combined alice_base for NN
            pps.extend(rc.get_all_pps())

            for k, v in rc.J_pps.items():
                new_key = f"{rc.name}_{rc.N}_{k}"
                if k not in combined_alice_base_J_pps:
                    combined_alice_base_J_pps[new_key] = PlotProperties(f"{rc.name}/N{rc.N}/{k}_vs_J.png")

                combined_alice_base_J_pps[new_key].update_x("J", v.x_vals)
                y_vals, y_lim = v.ys["a=0"]
                combined_alice_base_J_pps[new_key].update_ys(k, f"a=0, alice_basis={rc.alice_basis}", y_vals, y_lim)
                y_vals, y_lim = v.ys["a=1"]
                combined_alice_base_J_pps[new_key].update_ys(k, f"a=1, alice_basis={rc.alice_basis}", y_vals, y_lim)
            
            for k, v in rc.h_pps.items():
                new_key = f"{rc.name}_{rc.N}_{k}"
                if k not in combined_alice_base_h_pps:
                    combined_alice_base_h_pps[new_key] = PlotProperties(f"{rc.name}/N{rc.N}/{k}_vs_h.png")

                combined_alice_base_h_pps[new_key].update_x("h", v.x_vals)
                y_vals, y_lim = v.ys["a=0"]
                combined_alice_base_h_pps[new_key].update_ys(k, f"a=0, alice_basis={rc.alice_basis}", y_vals, y_lim)
                y_vals, y_lim = v.ys["a=1"]
                combined_alice_base_h_pps[new_key].update_ys(k, f"a=1, alice_basis={rc.alice_basis}", y_vals, y_lim)

        pps.extend(combined_alice_base_J_pps.values())
        pps.extend(combined_alice_base_h_pps.values())
        pps.extend(class_comm_vs_N_pps.values())

    for pp in pps:
        pp.plot()
