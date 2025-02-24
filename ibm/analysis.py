from datetime import datetime
from qiskit.visualization import plot_histogram, circuit_drawer
from qiskit.quantum_info import concurrence
import os


class Analyzer:
    run_time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

    def __init__(self, h, k, subfolder):
        self.directory = f'artifacts/{Analyzer.run_time}/h-{h}_k-{k}/{subfolder}'
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

    def _calc_expectations(self, h1_counts, v_counts, total_shots):
        z_expectation = 0
        xx_expectation = 0

        if h1_counts:
            for key, count in h1_counts.items():
                if key[1] == '0':  # Check the second bit for <H1>
                    z_expectation += count
                else:
                    z_expectation -= count

            z_expectation /= total_shots

        if v_counts:
            for key, count in v_counts.items():
                if key in ('11', '00'):
                    xx_expectation += count
                else:
                    xx_expectation -= count
            
            xx_expectation /= total_shots

        E1 = z_expectation + xx_expectation

        return (E1, z_expectation, xx_expectation)

    def add_section(self, section_name):
        self.report_content.append(f'<h2>{section_name}</h2>')
        print(f'\n{section_name}\n')

    def print_rho(self, h1_rho, v_rho):
        h1_rho = h1_rho / h1_rho.trace()
        text = f'Validity: h1 - {h1_rho.is_valid()} v - {v_rho.is_valid()}'
        print(text)
        self.report_content.append(f'<p>{text}</p>')

        if h1_rho.is_valid():
            text = f'H1 concurrence {concurrence(h1_rho)}'
            print(text)
            self.report_content.append(f'<p>{text}</p>')

        if v_rho.is_valid():
            text = f'V concurrence {concurrence(v_rho)}'
            print(text)
            self.report_content.append(f'<p>{text}</p>')

    def print_expectations(self, h1_counts, v_counts, total_shots, p_dephase):
        E1, z_expectation, xx_expectation = self._calc_expectations(h1_counts, v_counts, total_shots)
        text = f'For p_dephase = {p_dephase}: H1 = {z_expectation} ; V = {xx_expectation} ; E1 = {E1}'
        print(text)
        self.report_content.append(f'<p>{text}</p>')

    def create_histograms(self, h1_counts_list, v_counts_list, legend, colors, total_shots, p_dephase):
        if not h1_counts_list:
            return
        
        if not (len(h1_counts_list) == len(v_counts_list) == len(legend) == len(colors)):
            return

        h1_prob_list = [{k: v / total_shots for k, v in h1_counts.items()} for h1_counts in h1_counts_list]
        h1_filename = self._build_filename('h1_hist', p_dephase)
        plot_histogram(h1_prob_list, legend=legend, color=colors,
                       title=self._build_title('Z (H1) Classical bits results', p_dephase),
                       filename=h1_filename)
        self.report_content.append(f'<img src="{os.getcwd()}/{h1_filename}" alt="H1 Histogram">')

        v_prob_list = [{k: v / total_shots for k, v in v_counts.items()} for v_counts in v_counts_list]
        v_filename = self._build_filename('v_hist', p_dephase)
        plot_histogram(v_prob_list, legend=legend, color=colors,
                       title=self._build_title('XX (V) Classical bits results', p_dephase),
                       filename=v_filename)
        self.report_content.append(f'<img src="{os.getcwd()}/{v_filename}" alt="V Histogram">')

    def print_results(self, result_h1, result_v):
        text_h1 = f'H1 Results:\nH1 = {result_h1._pub_results[0].data["evs"][0]} +- {result_h1._pub_results[0].data["stds"][0]}'
        text_v = f'V Results:\nV = {result_v._pub_results[0].data["evs"][0]} +- {result_v._pub_results[0].data["stds"][0]}'
        print(text_h1)
        print()
        print(text_v)
        self.report_content.append(f'<p>{text_h1}</p>')
        self.report_content.append(f'<p>{text_v}</p>')

    def draw_circuit(self, qc):
        filename = self._build_filename(qc.name)
        circuit_drawer(qc, output='mpl', filename=filename)
        self.report_content.append(f'<img src="{os.getcwd()}/{filename}" alt="Circuit Diagram">')
        return filename

    def hist(self, counts, name, p_dephase):
        title = self._build_title(f'{name} Simulation results', p_dephase, 'qasm_simulator')
        print(title)
        print(counts)
        filename = self._build_filename(f'{name}_sim', p_dephase)
        plot_histogram(counts,
                       title=title,
                       filename=filename)
        self.report_content.append(f'<p>{title}</p>')
        self.report_content.append(f'<img src="{os.getcwd()}/{filename}" alt="Simulation Results">')

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
