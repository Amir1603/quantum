from observable import Observable
import matplotlib.pyplot as plt

class Results:
    def __init__(self, run_time):
        self.data = {}
        self.run_time = run_time

    def add_result(self, source, h, k, p_dephase, counts, expectation, obs: Observable):
        key = (h, k, obs.name)
        if key not in self.data:
            self.data[key] = {
                'counts': [],
                'expectation': [],
                'p_dephase': [],
                'source': [],
            }
        self.data[key]['counts'].append(counts)
        self.data[key]['expectation'].append(expectation)
        self.data[key]['p_dephase'].append(p_dephase)
        self.data[key]['source'].append(source)

    def generate_counts_graphs(self):
        num_plots = len(self.data)
        fig, axs = plt.subplots(num_plots, 2, figsize=(15, 5 * num_plots))
        fig.suptitle('Counts vs Dephasing Noise')

        for idx, ((h, k), data) in enumerate(self.data.items()):
            ax_h1 = axs[idx, 0]
            ax_v = axs[idx, 1]

            # Plot h1_counts
            for key in data['h1_counts'][0].keys():
                counts = [h1_counts[key] for h1_counts in data['h1_counts']]
                ax_h1.plot(data['p_dephase'], counts, marker='o', label=f'{key}')
            ax_h1.set_title(f'H1 Counts for (h={h}, k={k})')
            ax_h1.set_xlabel('Dephasing Noise')
            ax_h1.set_ylabel('Counts')
            ax_h1.legend()

            # Plot v_counts
            for key in data['v_counts'][0].keys():
                counts = [v_counts[key] for v_counts in data['v_counts']]
                ax_v.plot(data['p_dephase'], counts, marker='o', label=f'{key}')
            ax_v.set_title(f'V Counts for (h={h}, k={k})')
            ax_v.set_xlabel('Dephasing Noise')
            ax_v.set_ylabel('Counts')
            ax_v.legend()

        plt.tight_layout(rect=[0, 0, 1, 0.96])
        plt.savefig(f'artifacts/{self.run_time}/counts_vs_dephasing_noise.png')
        plt.show()

    def generate_expectation_graphs(self):
        fig, axs = plt.subplots(3, 1, figsize=(10, 12))
        fig.suptitle('Expectation Values vs Dephasing Noise')

        for (h, k), data in self.data.items():
            label = f'h={h}, k={k}'

            # Plot H1 expectation values
            axs[0].plot(data['p_dephase'], data['h1_expectations'], marker='o', label=label)
            axs[0].set_title('H1 Expectation vs Dephasing Noise')
            axs[0].set_xlabel('Dephasing Noise')
            axs[0].set_ylabel('H1 Expectation')
            axs[0].legend()

            # Plot V expectation values
            axs[1].plot(data['p_dephase'], data['v_expectations'], marker='o', label=label)
            axs[1].set_title('V Expectation vs Dephasing Noise')
            axs[1].set_xlabel('Dephasing Noise')
            axs[1].set_ylabel('V Expectation')
            axs[1].legend()

            # Plot E expectation values
            axs[2].plot(data['p_dephase'], data['e_expectations'], marker='o', label=label)
            axs[2].set_title('E Expectation vs Dephasing Noise')
            axs[2].set_xlabel('Dephasing Noise')
            axs[2].set_ylabel('E Expectation')
            axs[2].legend()

        plt.tight_layout(rect=[0, 0, 1, 0.96])
        plt.savefig(f'artifacts/{self.run_time}/expectation_graphs.png')
        plt.show()
