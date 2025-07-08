import matplotlib.pyplot as plt
import numpy as np
from Calculators import Operators, NumericalTFIM
import utils
from conf import Conf, ErrorsConf
import os


# Collect and deduplicate legend handles and labels
def get_unique_legend(ax_array):
    seen = set()
    unique_handles = []
    unique_labels = []
    for ax in ax_array.flat:
        handles, labels = ax.get_legend_handles_labels()
        for h, l in zip(handles, labels):
            if l not in seen:
                unique_handles.append(h)
                unique_labels.append(l)
                seen.add(l)
    return unique_handles, unique_labels


def single_run(conf: Conf, alice_base: utils.AliceBase, OB_classes: list[type]):
    OBs = {OB_class.__name__: OB_class(conf.h, conf.J, conf.N, alice_base) for OB_class in OB_classes}
    H = hamiltonian_class(conf.h, conf.J, conf.N)

    ntfim = NumericalTFIM(H, list(OBs.values()))
    ntfim.calc_all(conf)

    return OBs

def run_Js(conf: Conf, i: int, N: int, alice_base: utils.AliceBase, OB_classes: list[type], tel_axis):
    teleported_values = {}
    confs = Conf.generate_J_for_h(conf, 250, False)
    Js = [c.J for c in confs]

    for c in confs:
        OBs = single_run(c, alice_base, OB_classes)

        for k, v in OBs.items():
            if k not in teleported_values:
                teleported_values[k] = []

            teleported_values[k].append(v.teleported_values)

    for idx, k in enumerate(teleported_values):
        a0_vals = [tv[False] for tv in teleported_values[k]]
        a1_vals = [tv[True] for tv in teleported_values[k]]

        tel_axis[idx, i].plot(Js, a0_vals, label=f'a=0, sigma_A={alice_base}')
        tel_axis[idx, i].plot(Js, a1_vals, label=f'a=1, sigma_A={alice_base}')
        tel_axis[idx, i].set_title(f"{k} N={N}")

errors = {
    'p_classical_error': ErrorsConf.generate_classical_error,
    'p_depol_error': ErrorsConf.generate_depolarization_error,
    'p_bitflip_error': ErrorsConf.generate_bitflip_error,
    'p_alice_phaseflip_error': ErrorsConf.generate_alice_phase_flip_error,
    'p_bob_phaseflip_error': ErrorsConf.generate_bob_phase_flip_error,
    'p_excited_mixture_error': ErrorsConf.generate_excited_mixture_error,
    'p_excited_superposition_error': ErrorsConf.generate_excited_superposition_error,
}

def run_errors(conf: Conf, i: int, N: int, alice_base: utils.AliceBase, OB_classes: list[type], errs_axis):
    Js = np.linspace(1.0, 4.0, 7).tolist()

    for j, (name, generate_err) in enumerate(errors.items()):
        for J in Js:
            conf.J = J
            teleported_values = {}

            errs = generate_err()
            confs = [c for c in Conf.generate_from_errors(conf, errs)]

            for c in confs:
                OBs = single_run(c, alice_base, OB_classes)

                for k, v in OBs.items():
                    if k not in teleported_values:
                        teleported_values[k] = []

                    teleported_values[k].append(v.teleported_values)

            for idx, k in enumerate(teleported_values):
                a0_vals = [tv[False] for tv in teleported_values[k]]

                p_errs = [err_conf.__dict__[name] for err_conf in errs]
                errs_axis[j][idx, i].plot(p_errs, a0_vals, label=f'J={J}')
                errs_axis[j][idx, i].set_title(f"{k} N={N}")


if __name__ == "__main__":
    h = 1.0

    hamiltonians = {
        'alice': (Operators.alice_H, [Operators.alice_HB, Operators.QB], [utils.AliceBase.X], [1, 2, 3, 4]),
        'nn': (Operators.nn_H, [Operators.nn_HB, Operators.QB], [utils.AliceBase.X, utils.AliceBase.Y], [2, 3, 4]),
        'nn_X': (Operators.nn_H, [Operators.nn_HB, Operators.QB], [utils.AliceBase.X], [2, 3, 4]),
        'nn_Y': (Operators.nn_H, [Operators.nn_HB, Operators.QB], [utils.AliceBase.Y], [2, 3, 4]),
    }

    for name, (hamiltonian_class, OB_classes, alice_bases, Ns) in hamiltonians.items():
        # Teleported figure
        tel_figure, tel_axis = plt.subplots(2, len(Ns), figsize=(10, 6))
        tel_figure.subplots_adjust(right=0.8)
        for ax in tel_axis.flat:
            ax.set_title("", fontsize=10)

        # Errors figure
        errs_plot = {}
        for err_name in errors.keys():
            err_figure, err_axis = plt.subplots(2, len(Ns), figsize=(10, 6))
            err_figure.subplots_adjust(right=0.8)
            for ax in err_axis.flat:
                ax.set_title("", fontsize=10)
            
            errs_plot[err_name] = err_figure, err_axis

        print(f"Calculating theoretical values for {name}...")

        for alice_base in alice_bases:
            for i, N in enumerate(Ns):
                print(f"Calculating for N={N} with AliceBase={alice_base}...")

                conf = Conf(N)
                conf.h = h
                conf.xor_alice_res = 0
                conf.errors = ErrorsConf()

                run_Js(conf, i, N, alice_base, OB_classes, tel_axis)

                errs_axis = [err_axis for _, err_axis in errs_plot.values()]
                run_errors(conf, i, N, alice_base, OB_classes, errs_axis)

        tel_handles, tel_labels = get_unique_legend(tel_axis)
        tel_figure.suptitle('Teleported operators expectation Values for Different N and J', fontsize=14)
        tel_figure.tight_layout(rect=[0, 0.05, 1, 0.93])
        tel_figure.legend(tel_handles, tel_labels, loc='upper center', bbox_to_anchor=(0.5, -0.02), ncol=3)
        tel_figure.savefig(f'artifacts/teleported_operators_{name}.png', bbox_inches='tight')
        plt.close(tel_figure)

        for err_name, (err_figure, err_axis) in errs_plot.items():
            err_handles, err_labels = get_unique_legend(err_axis)
            err_figure.suptitle(f'Teleported value vs. {err_name} for different Js', fontsize=14)
            err_figure.tight_layout(rect=[0, 0.05, 1, 0.93])
            err_figure.legend(err_handles, err_labels, loc='upper center', bbox_to_anchor=(0.5, -0.02), ncol=3)
            os.makedirs(f'artifacts/errors/{name}', exist_ok=True) 
            err_figure.savefig(f'artifacts/errors/{name}/{err_name}.png', bbox_inches='tight')
            plt.close(err_figure)
