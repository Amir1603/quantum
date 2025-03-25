from conf import Conf
from observable import Observable
from datetime import datetime
from qiskit.visualization import plot_histogram, circuit_drawer
from qiskit.quantum_info import concurrence
import os
import matplotlib.pyplot as plt
import math


class Analyzer:
    run_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    confs = []

    def save_conf(conf: Conf):
        Analyzer.confs.append(conf)

    def dump_confs():
        with open(f'artifacts/{Analyzer.run_time}/conf.txt', 'w') as f:
            f.write(str(Analyzer.confs))


    def __init__(self, h, k, p_dephase, delay, subfolder):
        self.directory = f'artifacts/{Analyzer.run_time}/h-{h}_k-{k}/{delay}/{p_dephase}/{subfolder}'
        os.makedirs(self.directory, exist_ok=False)
        self.report_content = []

    def _build_filename(self, header, p_dephase=None, suffix=None):
        dephase_str = str(p_dephase).replace('.', '_')
        extended_header = f'{self.directory}/{header}'

        if p_dephase and suffix:
            return f'{extended_header}_{dephase_str}_{suffix}.png'
        elif p_dephase and not suffix:
            return f'{extended_header}_{dephase_str}_{suffix}.png'
        elif not p_dephase and suffix:
            return f'{extended_header}_{suffix}.png'
        else:
            return f'{extended_header}.png'

    def _build_title(self, header, p_dephase, suffix=None):
        if p_dephase and suffix:
            return f'{header} for p_dephase={p_dephase} {suffix}'
        elif p_dephase and not suffix:
            return f'{header} for p_dephase={p_dephase}'
        elif not p_dephase and suffix:
            return f'{header} {suffix}'
        else:
            return f'{header}'

    def calc_expectation_and_sem(obs: Observable, counts, total_shots):
        """
        Calculates the expectation value and Standard Error of the Mean (SEM).

        Args:
            obs: An Observable object with a get_value(bitstring) method.
            counts: A dictionary from the simulator/hardware {bitstring: count}.
            total_shots: The total number of shots executed.

        Returns:
            A tuple: (expectation_value, standard_error_of_mean)
                    Returns (0, 0) if counts is empty or total_shots is 0.
        """
        if not counts or total_shots == 0:
            return 0.0, 0.0

        sum_val = 0.0
        sum_val_sq = 0.0

        for bitstring, count in counts.items():
            value = obs.get_value(bitstring)
            sum_val += value * count
            sum_val_sq += (value**2) * count

        # Calculate expectation value <O>
        expectation = sum_val / total_shots

        # Calculate <O^2>
        expectation_sq = sum_val_sq / total_shots

        # Calculate variance: Var(O) = <O^2> - <O>^2
        # Use max(0, ...) to prevent small negative variance due to floating point errors
        variance = max(0.0, expectation_sq - expectation**2)

        # Calculate standard deviation
        std_dev = math.sqrt(variance)

        # Calculate Standard Error of the Mean (SEM) = std_dev / sqrt(N)
        # Handle division by zero if total_shots is somehow 1 or less after filtering
        if total_shots <= 1:
            sem = std_dev # Or arguably undefined/NaN, but returning std_dev is safer
        else:
            sem = std_dev / math.sqrt(total_shots)

        return expectation, sem

    def add_section(self, section_name, qc=None):
        self.report_content.append(f'<h2>{section_name}</h2>')
        print(f'\n{section_name}\n')

        if qc:
            self._draw_circuit(qc)

    def print_rho(self, rho, obs: Observable):
        rho = rho / rho.trace()
        text = f'Validity: {obs.name} - {rho.is_valid()}'
        print(text)
        self.report_content.append(f'<p>{text}</p>')

        if rho.is_valid():
            text = f'{obs.description()} concurrence {concurrence(rho)}'
            print(text)
            self.report_content.append(f'<p>{text}</p>')

    def print_expectation(self, expectation, counts, p_dephase, obs: Observable):
        text = f'For p_dephase = {p_dephase}:'
        print(text)
        self.report_content.append(f'<p>{text}</p>')
        
        text = f'{obs.name} Counts: {counts}'
        print(text)
        self.report_content.append(f'<p>{text}</p>')

        text = f'{obs.name} Expectation = {expectation[0]} ± {expectation[1]}'
        print(text)
        self.report_content.append(f'<p>{text}</p>')

        corr = Analyzer.calculate_correlation(counts)
        text = f'{obs.name} Correlation = {corr}'
        print(text)
        self.report_content.append(f'<p>{text}</p>')

        print(obs.get_extra_info(counts))
        self.report_content.append(f'<p>{obs.get_extra_info(counts)}</p>')

    def create_histogram(self, counts_list, legend, total_shots, p_dephase):
        if not counts_list:
            return
        
        if not (len(counts_list) == len(legend)):
            return

        prob_list = [{k: v / total_shots for k, v in counts.items()} for counts in counts_list]
        filename = self._build_filename(f'counts_hist', p_dephase)
        plot_histogram(prob_list, legend=legend,
                       title=self._build_title(f'Classical bits results', p_dephase))
        plt.savefig(filename, bbox_inches="tight")
        self.report_content.append(f'<img src="{os.getcwd()}/{filename}" alt="Counts Histogram">')

    def hist(self, counts, name, p_dephase):
        title = self._build_title(f'{name} Simulation results', p_dephase, 'qasm_simulator')
        filename = self._build_filename(f'{name}_sim', p_dephase)
        probs = {k: v / sum(counts.values()) for k, v in counts.items()}

        print(title)
        plot_histogram(probs,
                       title=title,
                       filename=filename)
        self.report_content.append(f'<p>{title}</p>')

    def _draw_circuit(self, qc):
        filename = self._build_filename(qc.name)
        circuit_drawer(qc, output='mpl', filename=filename)
        self.report_content.append(f'<img src="{os.getcwd()}/{filename}" alt="Circuit Diagram">')
        return filename

    def generate_html_report(self):
        html_content = """
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Quantum Experiment Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; }
                img { max-width: 100%; height: auto; }
                .content { margin-bottom: 20px; }
            </style>
        </head>
        <body>
            <h1>Quantum Experiment Report</h1>
        """

        for content in self.report_content:
            html_content += f'<div class="content">{content}</div>\n'

        html_content += """
        </body>
        </html>
        """

        html_output = f'{self.directory}/report.html'
        with open(html_output, 'w') as f:
            f.write(html_content)
        print(f'Report saved as {html_output}')

    def calculate_correlation(counts):
        """
        Calculates the correlation between Alice's and Bob's measurement results.

        The correlation is calculated based on the expectation values of Alice's
        and Bob's measurements. For simplicity, let's assume Alice and Bob both
        measure in the Z-basis, so the outcomes are 0 and 1. We map these to +1
        and -1, respectively.

        Correlation = <Alice * Bob>

        Args:
            counts (dict): Counts of measurement outcomes.

        Returns:
            float: The calculated correlation between Alice's and Bob's results.
        """

        total_counts = sum(counts.values())  # Assuming same total for Bob

        correlation = 0
        for outcome, count in counts.items():
            alice_outcome = 1 if outcome[0] == '0' else -1  # Map 0 to +1, 1 to -1
            bob_outcome = 1 if outcome[1] == '0' else -1
            correlation += alice_outcome * bob_outcome * count / total_counts

        return correlation
