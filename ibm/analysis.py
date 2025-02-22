from qiskit.visualization import plot_histogram

def calc_expectations(h1_counts, v_counts, total_shots):
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


# Call twice - sim + hw
def print_expectations(h1_counts, v_counts, total_shots, p_dephase):
    E1, z_expectation, xx_expectation = calc_expectations(h1_counts, v_counts, total_shots)
    print(f'For p_dephase = {p_dephase}:\t<H1> = {z_expectation}\t<V> = {xx_expectation}\t<E1> = {E1}')


def create_histograms(h1_counts_list, v_counts_list, legend, colors, total_shots, p_dephase):
    if not h1_counts_list:
        return
    
    if not (len(h1_counts_list) == len(v_counts_list) == len(legend) == len(colors)):
        return

    dephase_str = str(p_dephase).replace('.', '_')

    h1_prob_list = [{k: v / total_shots for k, v in h1_counts.items()} for h1_counts in h1_counts_list]
    plot_histogram(h1_prob_list, legend=legend, color=colors, title=f"Z (H1) Classical bits results for p_dephase={p_dephase}", filename=f'h1_hist_{dephase_str}')

    v_prob_list = [{k: v / total_shots for k, v in v_counts.items()} for v_counts in v_counts_list]
    plot_histogram(v_prob_list, legend=legend, color=colors, title=f"XX (V) Classical bits results for p_dephase={p_dephase}", filename=f'v_hist_{dephase_str}')


def print_results(result_h1, result_v):
    print('H1 Results:')
    print(f'<H1> = {result_h1._pub_results[0].data['evs'][0]} +- {result_h1._pub_results[0].data['stds'][0]}')

    print()

    print('V Results:')
    print(f'<V> = {result_v._pub_results[0].data['evs'][0]} +- {result_v._pub_results[0].data['stds'][0]}')
