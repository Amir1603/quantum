import matplotlib.pyplot as plt
import numpy as np
from Calculators import AliceNumericalTFIM, NN_NumericalTFIM

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

def alice_hb_a0(h, J, exp_vals):
    HB = h*exp_vals.Zbob + J*exp_vals.X0_Xbob

    N_H = -np.sqrt((h**2 + J**2)*(exp_vals.Zbob**2 + exp_vals.X0_Xbob**2))
    hb_a0_tilde = ((h*exp_vals.Zbob + J*exp_vals.X0_Xbob)**2 + (h*exp_vals.X0_Xbob - J*exp_vals.Zbob)**2) / N_H

    return hb_a0_tilde - HB

def alice_hb_a1(h, J, exp_vals):
    HB = h*exp_vals.Zbob + J*exp_vals.X0_Xbob

    N_H = -np.sqrt((h**2 + J**2)*(exp_vals.Zbob**2 + exp_vals.X0_Xbob**2))
    hb_a1_tilde = ((h*exp_vals.Zbob + J*exp_vals.X0_Xbob)**2 - (h*exp_vals.X0_Xbob - J*exp_vals.Zbob)**2) / N_H

    return hb_a1_tilde - HB

def nn_hb_a0_x(h, J, exp_vals):
    HB = h*exp_vals.Zbob + J*exp_vals.Xbobn_Xbob

    h_term = h**2 * (exp_vals.Zbob**2 + exp_vals.X0_Xbob**2)
    J_term = J**2 * (exp_vals.X0_Xbobn_Zbob**2 + exp_vals.Xbobn_Xbob**2)
    hJ_term = 2 * h * J * (exp_vals.Zbob * exp_vals.Xbobn_Xbob - exp_vals.X0_Xbob * exp_vals.X0_Xbobn_Zbob)

    N_H = -2 * np.sqrt(h_term + J_term + hJ_term)
    hb_a0_tilde = (h_term + J_term + hJ_term) / (N_H)

    return hb_a0_tilde - HB

def nn_hb_a1_x(h, J, exp_vals):
    HB = h*exp_vals.Zbob + J*exp_vals.Xbobn_Xbob

    h_term = h**2 * (exp_vals.Zbob**2 + exp_vals.X0_Xbob**2)
    J_term = J**2 * (exp_vals.X0_Xbobn_Zbob**2 + exp_vals.Xbobn_Xbob**2)
    hJ_term = 2 * h * J * (exp_vals.Zbob * exp_vals.Xbobn_Xbob - exp_vals.X0_Xbob * exp_vals.X0_Xbobn_Zbob)

    N_H = -2 * np.sqrt(h_term + J_term + hJ_term)

    h_term = h**2 * (exp_vals.Zbob**2 - exp_vals.X0_Xbob**2)
    J_term = J**2 * (exp_vals.Xbobn_Xbob**2 - exp_vals.X0_Xbobn_Zbob**2)
    hJ_term = 2 * h * J * (exp_vals.Zbob * exp_vals.Xbobn_Xbob + exp_vals.X0_Xbob * exp_vals.X0_Xbobn_Zbob)

    hb_a0_tilde = (h_term + J_term + hJ_term) / (N_H)

    return hb_a0_tilde - HB

def nn_hb_a0_y(h, J, exp_vals):
    HB = h*exp_vals.Zbob + J*exp_vals.Xbobn_Xbob

    N_H = -np.sqrt(exp_vals.Zbob**2 + exp_vals.Y0_Ybob**2)
    hb_a0_tilde = J*exp_vals.Xbobn_Xbob + h*(exp_vals.Zbob**2 + exp_vals.Y0_Ybob**2) / (N_H)

    return hb_a0_tilde - HB

def nn_hb_a1_y(h, J, exp_vals):
    HB = h*exp_vals.Zbob + J*exp_vals.Xbobn_Xbob

    N_H = -np.sqrt(exp_vals.Zbob**2 + exp_vals.Y0_Ybob**2)
    hb_a0_tilde = J*exp_vals.Xbobn_Xbob + h*(exp_vals.Zbob**2 - exp_vals.Y0_Ybob**2) / (N_H)

    return hb_a0_tilde - HB

##########################################################

def alice_qb_a0(exp_vals):
    QB = 0.5 * (1 + exp_vals.Zbob)

    N_q = -np.sqrt(exp_vals.Zbob**2 + exp_vals.X0_Xbob**2)
    QB_a0_tilde = 0.5 + (exp_vals.Zbob**2 + exp_vals.X0_Xbob**2) / (2 * N_q)

    return QB_a0_tilde - QB

def alice_qb_a1(exp_vals):
    QB = 0.5 * (1 + exp_vals.Zbob)

    N_q = -np.sqrt(exp_vals.Zbob**2 + exp_vals.X0_Xbob**2)
    QB_a1_tilde = 0.5 + (exp_vals.Zbob**2 - exp_vals.X0_Xbob**2) / (2 * N_q)

    return QB_a1_tilde - QB

def nn_qb_a0_x(exp_vals):
    QB = 0.5 * (1 + exp_vals.Zbob)

    N_q = -np.sqrt(exp_vals.Zbob**2 + exp_vals.X0_Xbob**2)
    QB_a1_tilde = 0.5 + (exp_vals.Zbob**2 - exp_vals.X0_Xbob**2) / (2 * N_q)

    return QB_a1_tilde - QB

def nn_qb_a1_x(exp_vals):
    return 0

def nn_qb_a0_y(exp_vals):
    return 0

def nn_qb_a1_y(exp_vals):
    return 0

##########################################################




if __name__ == "__main__":
    Ns = [1, 2]#, 3, 4]
    Js = np.linspace(0.0, 10.0, 250).tolist()
    h = 1.0

    ntfims = {
        # 'alice': AliceNumericalTFIM,
        'nn': NN_NumericalTFIM
    }

    for name, ntfim_class in ntfims.items():
        # Raw figure - multiple subplots in a 3x5 grid, remove unused subplot
        raw_figure, raw_axis = plt.subplots(3, 5, figsize=(10, 6))
        raw_figure.subplots_adjust(right=0.8)
        for ax in raw_axis.flat:
            ax.set_title("", fontsize=10)

        # Teleported figure
        tel_figure, tel_axis = plt.subplots(2, len(Ns), figsize=(10, 6))
        tel_figure.subplots_adjust(right=0.8)
        for ax in tel_axis.flat:
            ax.set_title("", fontsize=10)

        print(f"Calculating theoretical values for {name}...")

        for i, N in enumerate(Ns):
            print(f"Calculating for N={N}...")

            X0 = []
            Y0 = []
            Xbob = []
            Ybob = []
            Zbob = []
            X0_Xbob = []
            Y0_Ybob = []
            X0_Zbob = []
            Y0_Zbob = []
            Xbobn_Xbob = []
            Xbobn_Zbob = []
            X0_Xbobn_Zbob = []
            X0_Xbobn_Xbob = []
            Y0_Xbobn_Xbob = []

            HB_a0_x = []
            HB_a1_x = []
            QB_a0_x = []
            QB_a1_x = []
            HB_a0_y = []
            HB_a1_y = []
            QB_a0_y = []
            QB_a1_y = []

            for J in Js:
                ntfim = ntfim_class(N, J, h)
                ntfim.calc_all()

                exp_vals = ntfim.get_expectation_values()

                X0.append(exp_vals.X0)
                Y0.append(exp_vals.Y0)
                Xbob.append(exp_vals.Xbob)
                Ybob.append(exp_vals.Ybob)
                Zbob.append(exp_vals.Zbob)
                X0_Xbob.append(exp_vals.X0_Xbob)
                Y0_Ybob.append(exp_vals.Y0_Ybob)
                X0_Zbob.append(exp_vals.X0_Zbob)
                Y0_Zbob.append(exp_vals.Y0_Zbob)
                Xbobn_Xbob.append(exp_vals.Xbobn_Xbob)
                Xbobn_Zbob.append(exp_vals.Xbobn_Zbob)
                X0_Xbobn_Zbob.append(exp_vals.X0_Xbobn_Zbob)
                X0_Xbobn_Xbob.append(exp_vals.X0_Xbobn_Xbob)
                Y0_Xbobn_Xbob.append(exp_vals.Y0_Xbobn_Xbob)

                if name == 'alice':
                    HB_a0_x.append(alice_hb_a0(h, J, exp_vals))
                    HB_a1_x.append(alice_hb_a1(h, J, exp_vals))
                    HB_a0_y.append(0)
                    HB_a1_y.append(0)

                    # QB is only defined for J != 0
                    if J != 0:
                        QB_a0_x.append(alice_qb_a0(exp_vals))
                        QB_a1_x.append(alice_qb_a1(exp_vals))
                        QB_a1_y.append(0)
                        QB_a1_y.append(0)

                else:
                    HB_a0_x.append(nn_hb_a0_x(h, J, exp_vals))
                    HB_a1_x.append(nn_hb_a1_x(h, J, exp_vals))
                    HB_a0_y.append(nn_hb_a0_y(h, J, exp_vals))
                    HB_a1_y.append(nn_hb_a1_y(h, J, exp_vals))

                    # QB is only defined for J != 0
                    if J != 0:
                        QB_a0_x.append(nn_qb_a0_x(exp_vals))
                        QB_a1_x.append(nn_qb_a1_x(exp_vals))
                        QB_a0_y.append(nn_qb_a0_y(exp_vals))
                        QB_a1_y.append(nn_qb_a1_y(exp_vals))

            raw_axis[0, 0].plot(Js, Xbob, label=f'N={N}')
            raw_axis[0, 0].set_title("Xbob")
            raw_axis[0, 1].plot(Js, Ybob, label=f'N={N}')
            raw_axis[0, 1].set_title("Ybob")
            raw_axis[0, 2].plot(Js, Zbob, label=f'N={N}')
            raw_axis[0, 2].set_title("Zbob")
            raw_axis[0, 3].plot(Js, X0, label=f'N={N}')
            raw_axis[0, 3].set_title("X0")
            raw_axis[0, 4].plot(Js, Y0, label=f'N={N}')
            raw_axis[0, 4].set_title("Y0")
            raw_axis[1, 0].plot(Js, X0_Xbob, label=f'N={N}')
            raw_axis[1, 0].set_title("X0 Xbob")
            raw_axis[1, 1].plot(Js, Y0_Ybob, label=f'N={N}')
            raw_axis[1, 1].set_title("Y0 Ybob")
            raw_axis[1, 2].plot(Js, X0_Zbob, label=f'N={N}')
            raw_axis[1, 2].set_title("X0 Zbob")
            raw_axis[1, 3].plot(Js, Y0_Zbob, label=f'N={N}')
            raw_axis[1, 3].set_title("Y0 Zbob")
            raw_axis[1, 4].plot(Js, Xbobn_Xbob, label=f'N={N}')
            raw_axis[1, 4].set_title("Xbobn Xbob")
            raw_axis[2, 0].plot(Js, Xbobn_Zbob, label=f'N={N}')
            raw_axis[2, 0].set_title("Xbobn Zbob")
            raw_axis[2, 1].plot(Js, X0_Xbobn_Zbob, label=f'N={N}')
            raw_axis[2, 1].set_title("X0 Xbobn Zbob")
            raw_axis[2, 2].plot(Js, X0_Xbobn_Xbob, label=f'N={N}')
            raw_axis[2, 2].set_title("X0 Xbobn Xbob")
            raw_axis[2, 3].plot(Js, Y0_Xbobn_Xbob, label=f'N={N}')
            raw_axis[2, 3].set_title("Y0 Xbobn Xbob")

            tel_axis[0, i].plot(Js, HB_a0_x, label=f'a=0, X')
            tel_axis[0, i].plot(Js, HB_a1_x, label=f'a=1, X')
            tel_axis[0, i].plot(Js, HB_a0_y, label=f'a=0, Y')
            tel_axis[0, i].plot(Js, HB_a1_y, label=f'a=1, Y')
            tel_axis[0, i].set_title(f"HB N={N}")

            # Remove J=0 from QB as it is not defined there
            tel_axis[1, i].plot(Js[1:], QB_a0_x, label=f'a=0')
            tel_axis[1, i].plot(Js[1:], QB_a1_x, label=f'a=1')
            tel_axis[1, i].set_title(f"QB N={N}")

        # Remove unused subplot from raw_axis (bottom right)
        raw_figure.delaxes(raw_axis[2, 4])  # remove the 15th placeholder

        # Add legends to the side of each figure (once only)
        raw_handles, raw_labels = get_unique_legend(raw_axis)
        raw_figure.suptitle('Raw operators expectation Values for Different N and J', fontsize=14)
        raw_figure.tight_layout(rect=[0, 0.05, 1, 0.93])  # Leave space at bottom for legend
        raw_figure.legend(raw_handles, raw_labels, loc='upper center', bbox_to_anchor=(0.5, -0.02), ncol=3)
        raw_figure.savefig(f'artifacts/raw_operators_{name}.png', bbox_inches='tight')

        tel_handles, tel_labels = get_unique_legend(tel_axis)
        tel_figure.suptitle('Teleported operators expectation Values for Different N and J', fontsize=14)
        tel_figure.tight_layout(rect=[0, 0.05, 1, 0.93])
        tel_figure.legend(tel_handles, tel_labels, loc='upper center', bbox_to_anchor=(0.5, -0.02), ncol=3)
        tel_figure.savefig(f'artifacts/teleported_operators_{name}.png', bbox_inches='tight')
