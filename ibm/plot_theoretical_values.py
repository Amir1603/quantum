import matplotlib.pyplot as plt
import numpy as np
from Calculators import NumericalTFIM

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
    Ns = [1, 2, 3, 4, 5, 6]
    Js = np.linspace(0.0, 4.0, 100).tolist()
    h = 1.0

    # Raw figure - 5 subplots in a 2x3 grid, remove unused subplot
    raw_figure, raw_axis = plt.subplots(2, 3, figsize=(10, 6))
    raw_figure.subplots_adjust(right=0.8)
    for ax in raw_axis.flat:
        ax.set_title("", fontsize=10)

    # Teleported figure - 4 subplots
    tel_figure, tel_axis = plt.subplots(2, 2, figsize=(10, 6))
    tel_figure.subplots_adjust(right=0.8)
    for ax in tel_axis.flat:
        ax.set_title("", fontsize=10)

    for N in Ns:

        X0 = []
        Xbob = []
        Zbob = []
        X0_Xbob = []
        X0_Zbob = []

        Hb0c0 = []
        Hb1c1 = []
        Hb0c1 = []
        Hb1c0 = []
        Qb0c0 = []
        Qb1c1 = []
        Qb0c1 = []
        Qb1c0 = []

        for J in Js:
            ntfim = NumericalTFIM(N, J, h)
            ntfim.calc_all()

            exp_vals = ntfim.get_expectation_values()

            X0.append(exp_vals['X0'])
            Xbob.append(exp_vals['Xbob'])
            Zbob.append(exp_vals['Zbob'])
            X0_Xbob.append(exp_vals['X0_Xbob'])
            X0_Zbob.append(exp_vals['X0_Zbob'])

            HB = h*exp_vals['Zbob'] + J*exp_vals['X0_Xbob']
            QB = 0.5 * (1 + exp_vals['Zbob'])

            A = exp_vals['Zbob']**2 + exp_vals['Xbob']**2 + exp_vals['X0_Xbob']**2 + exp_vals['X0_Zbob']**2
            Bp = exp_vals['Zbob']*exp_vals['X0_Zbob'] + exp_vals['Xbob']*exp_vals['X0_Xbob']
            Bm = exp_vals['Zbob']*exp_vals['X0_Zbob'] - exp_vals['Xbob']*exp_vals['X0_Xbob']

            HBb0c0 = 0.5*np.sqrt((h**2 + J**2)*(A + 2*Bp))
            HBb1c1 = 0.5*np.sqrt((h**2 + J**2)*(A - 2*Bp))
            HBb0c1 = -0.5*np.sqrt((h**2 + J**2)*(A + 2*Bp))
            HBb1c0 = -0.5*np.sqrt((h**2 + J**2)*(A - 2*Bp))
            QBb0c0 = 0.25*(1 + exp_vals['X0'] + np.sqrt(A + 2*Bp))
            QBb1c1 = 0.25*(1 - exp_vals['X0'] - np.sqrt(A - 2*Bp))
            QBb0c1 = 0.25*(1 + exp_vals['X0'] - np.sqrt(A + 2*Bp))
            QBb1c0 = 0.25*(1 - exp_vals['X0'] + np.sqrt(A - 2*Bp))

            Hb0c0.append((HBb0c0 - HB) / HB)
            Hb1c1.append((HBb1c1 - HB) / HB)
            Hb0c1.append((HBb0c1 - HB) / HB)
            Hb1c0.append((HBb1c0 - HB) / HB)
            Qb0c0.append((QBb0c0 - QB) / QB)
            Qb1c1.append((QBb1c1 - QB) / QB)
            Qb0c1.append((QBb0c1 - QB) / QB)
            Qb1c0.append((QBb1c0 - QB) / QB)

        raw_axis[0, 0].plot(Js, Xbob, label=f'N={N}')
        raw_axis[0, 0].set_title("Xbob")
        raw_axis[0, 1].plot(Js, Zbob, label=f'N={N}')
        raw_axis[0, 1].set_title("Zbob")
        raw_axis[1, 0].plot(Js, X0_Xbob, label=f'N={N}')
        raw_axis[1, 0].set_title("X0 Xbob")
        raw_axis[1, 1].plot(Js, X0_Zbob, label=f'N={N}')
        raw_axis[1, 1].set_title("X0 Zbob")
        raw_axis[0, 2].plot(Js, X0, label=f'N={N}')
        raw_axis[0, 2].set_title("X0")

        tel_axis[0, 0].plot(Js, Hb0c0, label=f'c=0, N={N}')
        tel_axis[0, 0].plot(Js, Hb0c1, label=f'c=1, N={N}')
        tel_axis[0, 0].set_title("HB (b = 0)")
        tel_axis[1, 0].plot(Js, Hb1c0, label=f'c=0, N={N}')
        tel_axis[1, 0].plot(Js, Hb1c1, label=f'c=1, N={N}')
        tel_axis[1, 0].set_title("HB (b = 1)")

        tel_axis[0, 1].plot(Js, Qb0c0, label=f'c=0, N={N}')
        tel_axis[0, 1].plot(Js, Qb0c1, label=f'c=1, N={N}')
        tel_axis[0, 1].set_title("QB (b = 0)")
        tel_axis[1, 1].plot(Js, Qb1c0, label=f'c=0, N={N}')
        tel_axis[1, 1].plot(Js, Qb1c1, label=f'c=1, N={N}')
        tel_axis[1, 1].set_title("QB (b = 1)")

    # Remove unused subplot from raw_axis (bottom right)
    raw_figure.delaxes(raw_axis[1, 2])  # remove the 6th placeholder

    # Add legends to the side of each figure (once only)
    raw_handles, raw_labels = get_unique_legend(raw_axis)
    raw_figure.suptitle('Raw operators expectation Values for Different N and J', fontsize=14)
    raw_figure.tight_layout(rect=[0, 0.05, 1, 0.93])  # Leave space at bottom for legend
    raw_figure.legend(raw_handles, raw_labels, loc='upper center', bbox_to_anchor=(0.5, -0.02), ncol=3)
    raw_figure.savefig('artifacts/raw_operators.png', bbox_inches='tight')

    tel_handles, tel_labels = get_unique_legend(tel_axis)
    tel_figure.suptitle('Teleported operators expectation Values for Different N and J', fontsize=14)
    tel_figure.tight_layout(rect=[0, 0.05, 1, 0.93])
    tel_figure.legend(tel_handles, tel_labels, loc='upper center', bbox_to_anchor=(0.5, -0.02), ncol=3)
    tel_figure.savefig('artifacts/teleported_operators.png', bbox_inches='tight')
