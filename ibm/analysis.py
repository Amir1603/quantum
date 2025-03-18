from conf import Conf
from observable import Observable
from datetime import datetime
from qiskit.visualization import plot_histogram, circuit_drawer
from qiskit.quantum_info import concurrence
import os


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

    def calc_expectation(self, obs: Observable, counts, total_shots):
        expectation = 0
        xx_expectation = 0

        if counts:
            for key, count in counts.items():
                if obs.is_positive_count(key):
                    expectation += count
                else:
                    expectation -= count

            expectation /= total_shots

        return expectation

    def add_section(self, section_name):
        self.report_content.append(f'<h2>{section_name}</h2>')
        print(f'\n{section_name}\n')

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

        text = f'{obs.name} Expectation = {expectation}'
        print(text)
        self.report_content.append(f'<p>{text}</p>')

    def create_histogram(self, counts_list, legend, colors, total_shots, p_dephase, obs: Observable):
        if not counts_list:
            return
        
        if not (len(counts_list) == len(legend) == len(colors)):
            return

        prob_list = [{k: v / total_shots for k, v in counts.items()} for counts in counts_list]
        filename = self._build_filename(f'{obs.name}_hist', p_dephase)
        plot_histogram(prob_list, legend=legend, color=colors,
                       title=self._build_title(f'{obs.description()} Classical bits results', p_dephase),
                       filename=filename)
        self.report_content.append(f'<img src="{os.getcwd()}/{filename}" alt="{obs.name} Histogram">')

    def hist(self, counts, name, p_dephase):
        title = self._build_title(f'{name} Simulation results', p_dephase, 'qasm_simulator')
        filename = self._build_filename(f'{name}_sim', p_dephase)
        probs = {k: v / sum(counts.values()) for k, v in counts.items()}

        print(title)
        print(probs)
        plot_histogram(probs,
                       title=title,
                       filename=filename)
        self.report_content.append(f'<p>{title}</p>')
        self.report_content.append(f'<p>{probs}</p>')

    def draw_circuit(self, qc):
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
