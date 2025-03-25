from Observables import Observable, ObservableFactory
import matplotlib.pyplot as plt

class Results:
    def __init__(self, run_time):
        self.data = {}
        self.run_time = run_time

    def add_result(self, source, h, k, p_dephase, counts, expectation, obs: Observable):
        if obs.name not in self.data:
            self.data[obs.name] = {}

        key = (h, k)
        if key not in self.data[obs.name]:
            self.data[obs.name][key] = {
                'counts': [],
                'expectation': [],
                'p_dephase': [],
                'source': [],
            }
        self.data[obs.name][key]['counts'].append(counts)
        self.data[obs.name][key]['expectation'].append(expectation)
        self.data[obs.name][key]['p_dephase'].append(p_dephase)
        self.data[obs.name][key]['source'].append(source)

    def generate_counts_graphs(self):
        of = ObservableFactory()
        num_plots = len(self.data[of.obs_list[0].name])

        fig, axs = plt.subplots(num_plots, len(of.obs_list), figsize=(15, 5 * num_plots))
        fig.suptitle('Counts vs Dephasing Noise')

        for obs, obs_data in self.data.items():
            for idx, ((h, k), data) in enumerate(obs_data.items()):
                [i] = [index for index, element in enumerate(of.obs_list) if element.name == obs]
                if num_plots == 1:
                    ax = axs[i]
                else:
                    ax = axs[idx, i]

                # Plot counts
                for key in data['counts'][0].keys():
                    counts = [counts[key] for counts in data['counts']]
                    ax.plot(data['p_dephase'], counts, marker='o', label=f'{key}')
                ax.set_title(f'{obs} Counts for (h={h}, k={k})')
                ax.set_xlabel('Dephasing Noise')
                ax.set_ylabel('Counts')
                ax.legend()

        plt.tight_layout(rect=[0, 0, 1, 0.96])
        plt.savefig(f'artifacts/{self.run_time}/counts_vs_dephasing_noise.png')
        plt.show()

    def generate_expectation_graphs(self):
        of = ObservableFactory()
        fig, axs = plt.subplots(len(of.obs_list), 1, figsize=(10, 12))
        fig.suptitle('Expectation Values vs Dephasing Noise')

        for obs, obs_data in self.data.items():
            for (h, k), data in obs_data.items():
                label = f'h={h}, k={k}'

                # Plot expectation 
                [i] = [index for index, element in enumerate(of.obs_list) if element.name == obs]
                axs[i].plot(data['p_dephase'], data['expectation'], marker='o', label=label)
                axs[i].set_title(f'{obs} Expectation vs Dephasing Noise')
                axs[i].set_xlabel('Dephasing Noise')
                axs[i].set_ylabel(f'{obs} Expectation')
                axs[i].legend()

        plt.tight_layout(rect=[0, 0, 1, 0.96])
        plt.savefig(f'artifacts/{self.run_time}/expectation_graphs.png')
        plt.show()
