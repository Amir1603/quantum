import matplotlib.pyplot as plt
import numpy as np
from Calculators import Operators, NumericalTFIM
import utils


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


if __name__ == "__main__":
    Ns = [1, 2, 3, 4]
    Js = np.linspace(0.0, 10.0, 250).tolist()
    h = 1.0

    hamiltonians = {
        'alice': (Operators.alice_H, [Operators.alice_HB, Operators.QB], utils.AliceBase.X),
        'nn_X': (Operators.nn_H, [Operators.nn_HB, Operators.QB], utils.AliceBase.X),
        'nn_Y': (Operators.nn_H, [Operators.nn_HB, Operators.QB], utils.AliceBase.Y),
    }

    for name, (hamiltonian_class, OB_classes, alice_base) in hamiltonians.items():
        # Teleported figure
        tel_figure, tel_axis = plt.subplots(2, len(Ns), figsize=(10, 6))
        tel_figure.subplots_adjust(right=0.8)
        for ax in tel_axis.flat:
            ax.set_title("", fontsize=10)

        print(f"Calculating theoretical values for {name}...")

        for i, N in enumerate(Ns):
            print(f"Calculating for N={N}...")

            teleported_values = {}

            for J in Js:
                OBs = {OB_class.__name__: OB_class(h, J, N, alice_base) for OB_class in OB_classes}
                H = hamiltonian_class(h, J, N)

                ntfim = NumericalTFIM(H, list(OBs.values()))
                ntfim.calc_all(None)

                for k, v in OBs.items():
                    if k not in teleported_values:
                        teleported_values[k] = []

                    teleported_values[k].append(v.teleported_values)

            for idx, k in enumerate(teleported_values):
                a0_vals = [tv[False] for tv in teleported_values[k]]
                a1_vals = [tv[True] for tv in teleported_values[k]]

                tel_axis[idx, i].plot(Js, a0_vals, label=f'a=0')
                tel_axis[idx, i].plot(Js, a1_vals, label=f'a=1')
                tel_axis[idx, i].set_title(f"{k} N={N}")

        tel_handles, tel_labels = get_unique_legend(tel_axis)
        tel_figure.suptitle('Teleported operators expectation Values for Different N and J', fontsize=14)
        tel_figure.tight_layout(rect=[0, 0.05, 1, 0.93])
        tel_figure.legend(tel_handles, tel_labels, loc='upper center', bbox_to_anchor=(0.5, -0.02), ncol=3)
        tel_figure.savefig(f'artifacts/teleported_operators_{name}.png', bbox_inches='tight')
