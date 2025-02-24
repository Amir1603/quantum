from datetime import datetime
from qiskit.visualization import plot_histogram, circuit_drawer
from fpdf import FPDF
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
            return f'{extended_header}_{dephase_str}_{suffix}'
        elif p_dephase and not suffix:
            return f'{extended_header}_{dephase_str}_{suffix}'
        elif not p_dephase and suffix:
            return f'{extended_header}_{suffix}'
        else:
            return f'{extended_header}'

    def _build_title(self, header, p_dephase, suffix=None):
        if p_dephase and suffix:
            return f'{header} for p_dephase={p_dephase} {suffix}'
        elif p_dephase and not suffix:
            return f'{header} for p_dephase={p_dephase} {suffix}'
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

    def print_expectations(self, h1_counts, v_counts, total_shots, p_dephase):
        E1, z_expectation, xx_expectation = self._calc_expectations(h1_counts, v_counts, total_shots)
        text = f'For p_dephase = {p_dephase}:\t<H1> = {z_expectation}\t<V> = {xx_expectation}\t<E1> = {E1}'
        print(text)
        self.report_content.append(text)

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
        self.report_content.append(h1_filename)

        v_prob_list = [{k: v / total_shots for k, v in v_counts.items()} for v_counts in v_counts_list]
        v_filename = self._build_filename('v_hist', p_dephase)
        plot_histogram(v_prob_list, legend=legend, color=colors,
                       title=self._build_title('XX (V) Classical bits results', p_dephase),
                       filename=v_filename)
        self.report_content.append(v_filename)

    def print_results(self, result_h1, result_v):
        text_h1 = f'H1 Results:\n<H1> = {result_h1._pub_results[0].data["evs"][0]} +- {result_h1._pub_results[0].data["stds"][0]}'
        text_v = f'V Results:\n<V> = {result_v._pub_results[0].data["evs"][0]} +- {result_v._pub_results[0].data["stds"][0]}'
        print(text_h1)
        print()
        print(text_v)
        self.report_content.append(text_h1)
        self.report_content.append(text_v)

    def draw_circuit(self, qc):
        filename = self._build_filename(qc.name)
        circuit_drawer(qc, output='mpl', filename=filename)
        self.report_content.append(filename)
        return filename

    def hist(self, counts, name, p_dephase):
        title = self._build_title(f'{name} Simulation results', p_dephase)
        print(title)
        print(counts)
        filename = self._build_filename(f'{name}_sim', p_dephase)
        plot_histogram(counts,
                       title=title,
                       filename=filename)
        self.report_content.append(title)
        self.report_content.append(filename)

    def generate_pdf_report(self):
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        pdf.add_page()
        pdf.set_font("Arial", size=12)

        for content in self.report_content:
            if content.endswith('.png'):
                pdf.add_page()
                pdf.image(content, x=10, y=10, w=190)
            else:
                pdf.multi_cell(0, 10, content)

        pdf_output = f'{self.directory}/report.pdf'
        pdf.output(pdf_output)
        print(f'Report saved as {pdf_output}')
