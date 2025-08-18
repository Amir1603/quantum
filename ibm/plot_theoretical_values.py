import matplotlib.pyplot as plt
import numpy as np
from Calculators import Operators, NumericalTFIM
import utils
from conf import Conf, ErrorsConf
import os
from numerical_run_conf import NumericalRunConf
from plot_utils import add_avg_zero_vline_all_axes

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


def single_run(conf: Conf, alice_base: utils.AliceBase, hamiltonian_class: type, OB_classes: list[type]):
    OBs = {OB_class.__name__: OB_class(conf.h, conf.J, conf.N, alice_base) for OB_class in OB_classes}
    H = hamiltonian_class(conf.h, conf.J, conf.N)

    ntfim = NumericalTFIM(H, list(OBs.values()))
    ntfim.calc_all(conf)

    return OBs

def run_Js(i: int, N: int, alice_base: utils.AliceBase, hamiltonian_class: type, OB_classes: list[type], tel_axes):
    teleported_values = {}
    confs = Conf.generate_J_for_h(Conf(N), 100)
    Js = [c.J for c in confs]

    print(f"Running all Js ({len(Js)})")

    for c in confs:
        OBs = single_run(c, alice_base, hamiltonian_class, OB_classes)

        for k, v in OBs.items():
            if k not in teleported_values:
                teleported_values[k] = []

            teleported_values[k].append(v.teleported_values)

    for idx, k in enumerate(teleported_values):
        a0_vals = [tv[False] for tv in teleported_values[k]]
        a1_vals = [tv[True] for tv in teleported_values[k]]

        for tel_axis in tel_axes:
            tel_axis[idx, i].plot(Js, a0_vals, label=f'a=0, sigma_A={alice_base}')
            tel_axis[idx, i].plot(Js, a1_vals, label=f'a=1, sigma_A={alice_base}')
            tel_axis[idx, i].set_title(f"{k} N={N}")

def run_hs(i: int, N: int, alice_base: utils.AliceBase,  hamiltonian_class: type, OB_classes: list[type], tel_axes):
    teleported_values = {}
    confs = Conf.generate_h_for_J(Conf(N), 100)
    hs = [c.h for c in confs]

    print(f"Running all hs ({len(hs)})")

    for c in confs:
        OBs = single_run(c, alice_base, hamiltonian_class, OB_classes)

        for k, v in OBs.items():
            if k not in teleported_values:
                teleported_values[k] = []

            teleported_values[k].append(v.teleported_values)

    for idx, k in enumerate(teleported_values):
        a0_vals = [tv[False] for tv in teleported_values[k]]
        a1_vals = [tv[True] for tv in teleported_values[k]]

        for tel_axis in tel_axes:
            tel_axis[idx, i].plot(hs, a0_vals, label=f'a=0, sigma_A={alice_base}')
            tel_axis[idx, i].plot(hs, a1_vals, label=f'a=1, sigma_A={alice_base}')
            tel_axis[idx, i].set_title(f"{k} N={N}")

def run_single_error(err_name: str, conf: Conf, alice_base: utils.AliceBase, hamiltonian_class: type, OB_classes: list[type], errs_axis, label: str, i: int = None, add_N: bool = True):
    teleported_values = {}

    errs = NumericalRunConf.generate_errors_configurations(err_name)
    confs = [c for c in Conf.generate_from_errors(conf, errs)]

    for c in confs:
        OBs = single_run(c, alice_base,  hamiltonian_class, OB_classes)

        for k, v in OBs.items():
            if k not in teleported_values:
                teleported_values[k] = []

            teleported_values[k].append(v.teleported_values)

    for idx, k in enumerate(teleported_values):
        a0_vals = [tv[False] for tv in teleported_values[k]]

        p_errs = [err_conf.__dict__[err_name] for err_conf in errs]

        axis = errs_axis[idx, i] if i is not None else errs_axis[idx]

        axis.plot(p_errs, a0_vals, label=label)

        ylim = NumericalRunConf.get_ylim(err_name, k)
        if ylim and ylim[idx]:
            axis.set_ylim(ylim[idx])
        title = f"{k} N={conf.N}" if add_N else f"{k}"
        axis.set_title(f"{title}")

def run_errors(i: int, N: int, alice_base: utils.AliceBase,  hamiltonian_class: type, OB_classes: list[type], errs_axis):
    Js = np.linspace(1.0, 4.0, 7).tolist()
    print("Running all errors")

    for j, err_name in enumerate(NumericalRunConf.get_errors()):
        conf = Conf(N)

        for J in Js:
            conf.J = J
            run_single_error(err_name, conf, alice_base, hamiltonian_class, OB_classes, errs_axis[j], f'J={J}', i)

def run_class_comm_vs_N(alice_base: utils.AliceBase,  hamiltonian_class: type, OB_classes: list[type], errs_axis):
    Ns = list(range(2, 11))
    print("Running classical communication vs N")

    for N in Ns:
        conf = Conf(N)
        run_single_error('p_classical_error', conf, alice_base, hamiltonian_class, OB_classes, errs_axis, f'N={N}', add_N=False)

if __name__ == "__main__":
    run_confs = [
        NumericalRunConf.AliceConf(),
        NumericalRunConf.NNConf(),
    ]

    for run_conf in run_confs:
        # Teleported figure for both bases
        J_tel_figure_both_bases, J_tel_axis_both_bases = plt.subplots(2, len(run_conf.Ns), figsize=(10, 6))
        J_tel_figure_both_bases.subplots_adjust(right=0.8)
        for ax in J_tel_axis_both_bases.flat:
            ax.set_title("", fontsize=10)

        h_tel_figure_both_bases, h_tel_axis_both_bases = plt.subplots(2, len(run_conf.Ns), figsize=(10, 6))
        h_tel_figure_both_bases.subplots_adjust(right=0.8)
        for ax in h_tel_axis_both_bases.flat:
            ax.set_title("", fontsize=10)

        for alice_base in run_conf.alice_bases:
            # Teleported figure
            J_tel_figure, J_tel_axis = plt.subplots(2, len(run_conf.Ns), figsize=(10, 6))
            J_tel_figure.subplots_adjust(right=0.8)
            for ax in J_tel_axis.flat:
                ax.set_title("", fontsize=10)

            h_tel_figure, h_tel_axis = plt.subplots(2, len(run_conf.Ns), figsize=(10, 6))
            h_tel_figure.subplots_adjust(right=0.8)
            for ax in h_tel_axis.flat:
                ax.set_title("", fontsize=10)

            # Errors figure
            errs_plot = {}
            for err_name in NumericalRunConf.get_errors():
                err_figure, err_axis = plt.subplots(2, len(run_conf.Ns), figsize=(10, 6))
                err_figure.subplots_adjust(right=0.8)
                for ax in err_axis.flat:
                    ax.set_title("", fontsize=10)
                
                errs_plot[err_name] = err_figure, err_axis

            # Classical communication vs N figure
            class_err_figure, class_err_axis = plt.subplots(1, 2, figsize=(10, 6))
            class_err_figure.subplots_adjust(right=0.8)
            for ax in class_err_axis.flat:
                ax.set_title("", fontsize=10)

            print(f"Calculating theoretical values for {run_conf.name}...")

            for i, N in enumerate(run_conf.Ns):
                print(f"Calculating for N={N} with AliceBase={alice_base}...")

                run_Js(i, N, alice_base, run_conf.H_type, run_conf.OB_types, [J_tel_axis, J_tel_axis_both_bases])
                run_hs(i, N, alice_base, run_conf.H_type, run_conf.OB_types, [h_tel_axis, h_tel_axis_both_bases])

                errs_axis = [err_axis for _, err_axis in errs_plot.values()]
                run_errors(i, N, alice_base, run_conf.H_type, run_conf.OB_types, errs_axis)

            run_class_comm_vs_N(alice_base, run_conf.H_type, run_conf.OB_types, class_err_axis)

            J_tel_handles, J_tel_labels = get_unique_legend(J_tel_axis)
            J_tel_figure.suptitle('Teleported operators expectation Values for Different N and J', fontsize=14)
            J_tel_figure.tight_layout(rect=[0, 0.05, 1, 0.93])
            J_tel_figure.legend(J_tel_handles, J_tel_labels, loc='upper center', bbox_to_anchor=(0.5, -0.02), ncol=3)
            J_tel_figure.savefig(f'artifacts/teleported_operators_{run_conf.name}_{alice_base}_vs_J.png', bbox_inches='tight')
            plt.close(J_tel_figure)

            h_tel_handles, h_tel_labels = get_unique_legend(h_tel_axis)
            h_tel_figure.suptitle('Teleported operators expectation Values for Different N and h', fontsize=14)
            h_tel_figure.tight_layout(rect=[0, 0.05, 1, 0.93])
            h_tel_figure.legend(h_tel_handles, h_tel_labels, loc='upper center', bbox_to_anchor=(0.5, -0.02), ncol=3)
            h_tel_figure.savefig(f'artifacts/teleported_operators_{run_conf.name}_{alice_base}_vs_h.png', bbox_inches='tight')
            plt.close(h_tel_figure)

            for err_name, (err_figure, err_axis) in errs_plot.items():
                err_handles, err_labels = get_unique_legend(err_axis)
                add_avg_zero_vline_all_axes(err_figure, which='first', vline_kws={'color': 'black', 'linestyle': '--'})
                err_figure.suptitle(f'Teleported value vs. {err_name} for different Js', fontsize=14)
                err_figure.tight_layout(rect=[0, 0.05, 1, 0.93])
                err_figure.legend(err_handles, err_labels, loc='upper center', bbox_to_anchor=(0.5, -0.02), ncol=3)
                os.makedirs(f'artifacts/errors/{run_conf.name}_{alice_base}', exist_ok=True)
                err_figure.savefig(f'artifacts/errors/{run_conf.name}_{alice_base}/{err_name}.png', bbox_inches='tight')
                plt.close(err_figure)

        class_err_handles, class_err_labels = get_unique_legend(class_err_axis)
        add_avg_zero_vline_all_axes(class_err_figure, which='first', vline_kws={'color': 'black', 'linestyle': '--'})
        class_err_figure.suptitle(f'Teleported value vs. Classical Comm error for different Ns', fontsize=14)
        class_err_figure.tight_layout(rect=[0, 0.05, 1, 0.93])
        class_err_figure.legend(class_err_handles, class_err_labels, loc='upper center', bbox_to_anchor=(0.5, -0.02), ncol=3)
        os.makedirs(f'artifacts/errors/{run_conf.name}_{alice_base}', exist_ok=True)
        class_err_figure.savefig(f'artifacts/errors/{run_conf.name}_{alice_base}/teleported_vs_class_comm_for_Ns.png', bbox_inches='tight')
        plt.close(class_err_figure)

        J_tel_handles_both_bases, J_tel_labels_both_bases = get_unique_legend(J_tel_axis_both_bases)
        J_tel_figure_both_bases.suptitle('Teleported operators expectation Values for Different N and J', fontsize=14)
        J_tel_figure_both_bases.tight_layout(rect=[0, 0.05, 1, 0.93])
        J_tel_figure_both_bases.legend(J_tel_handles_both_bases, J_tel_labels_both_bases, loc='upper center', bbox_to_anchor=(0.5, -0.02), ncol=3)
        J_tel_figure_both_bases.savefig(f'artifacts/teleported_operators_{run_conf.name}_vs_J.png', bbox_inches='tight')
        plt.close(J_tel_figure_both_bases)

        h_tel_handles_both_bases, h_tel_labels_both_bases = get_unique_legend(h_tel_axis_both_bases)
        h_tel_figure_both_bases.suptitle('Teleported operators expectation Values for Different N and h', fontsize=14)
        h_tel_figure_both_bases.tight_layout(rect=[0, 0.05, 1, 0.93])
        h_tel_figure_both_bases.legend(h_tel_handles_both_bases, h_tel_labels_both_bases, loc='upper center', bbox_to_anchor=(0.5, -0.02), ncol=3)
        h_tel_figure_both_bases.savefig(f'artifacts/teleported_operators_{run_conf.name}_vs_h.png', bbox_inches='tight')
        plt.close(h_tel_figure_both_bases)
