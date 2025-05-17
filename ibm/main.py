import argparse
import os
from datetime import datetime
from conf import Conf
from Observables import ObservableFactory
from Calculators import NumericalTFIM, MyCalculatorTFIM, KazukiTFIM
from runner import Runner
from results import Results
import plotting
import reporting
from qiskit_ibm_runtime import QiskitRuntimeService


run_time_str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
output_dir = f'artifacts/{run_time_str}'
os.makedirs(output_dir, exist_ok=True)

# Create Results instance with output directory
res = Results(run_time_str, output_dir)

def print_run_plan(confs):
    print('#########################################################')
    print(f'Configurations to run: {len(confs)}')
    sim_count = sum(1 for c in confs if c.run_simulator)
    # Estimate sampler runs based on presence of p_dephase (can be refined)
    sampler_noise_count = sum(1 for c in confs if c.run_sampler and getattr(c, 'p_dephase', None) is not None) # Check attribute safely
    sampler_hw_count = sum(1 for c in confs if c.run_sampler and getattr(c, 'p_dephase', None) is None) # Assuming no p_dephase means hardware or ideal sim
    print(f'  Simulator runs: {sim_count}')
    print(f'  Sampler (sim w/ noise) runs: {sampler_noise_count}')
    print(f'  Sampler (HW/noiseless sim) runs: {sampler_hw_count}')
    print('#########################################################')


def report_and_plot(results_obj: Results, args):
    """Generates plots and the final HTML report."""
    results_list = results_obj.processed_results # Use the processed results list
    output_dir = results_obj.output_dir
    plot_filenames = [] # Collect paths to generated plots for the report

    if not results_list:
        print("No processed results to plot or report.")
        return

    # --- Plotting ---
    if args.N == 2:
        filter = {}
        # filter = {'conf_params.xor_alice_res': 0}

        energy_file = None
        charge_file = None

        if args.classical_errors:
            energy_file = plotting.plot_expectation_vs_parameter_filtered(results_list, output_dir, 'p_classical_error', filter, obs=['bobs_energy_n2'], group_by=['conf_params.J'])
            charge_file = plotting.plot_expectation_vs_parameter_filtered(results_list, output_dir, 'p_classical_error', filter, obs=['charge'], group_by=['conf_params.J'])
        elif args.depolarization_errors:
            energy_file = plotting.plot_expectation_vs_parameter_filtered(results_list, output_dir, 'p_depol_error', filter, obs=['bobs_energy_n2'], group_by=['conf_params.J'])
            charge_file = plotting.plot_expectation_vs_parameter_filtered(results_list, output_dir, 'p_depol_error', filter, obs=['charge'], group_by=['conf_params.J'])
        elif args.bit_flip_errors:
            energy_file = plotting.plot_expectation_vs_parameter_filtered(results_list, output_dir, 'p_bitflip_error', filter, obs=['bobs_energy_n2'], group_by=['conf_params.J'])
            charge_file = plotting.plot_expectation_vs_parameter_filtered(results_list, output_dir, 'p_bitflip_error', filter, obs=['charge'], group_by=['conf_params.J'])
        elif args.alice_phase_flip_errors:
            energy_file = plotting.plot_expectation_vs_parameter_filtered(results_list, output_dir, 'p_alice_phaseflip_error', filter, obs=['bobs_energy_n2'], group_by=['conf_params.J'])
            charge_file = plotting.plot_expectation_vs_parameter_filtered(results_list, output_dir, 'p_alice_phaseflip_error', filter, obs=['charge'], group_by=['conf_params.J'])
        elif args.bob_phase_flip_errors:
            energy_file = plotting.plot_expectation_vs_parameter_filtered(results_list, output_dir, 'p_bob_phaseflip_error', filter, obs=['bobs_energy_n2'], group_by=['conf_params.J'])
            charge_file = plotting.plot_expectation_vs_parameter_filtered(results_list, output_dir, 'p_bob_phaseflip_error', filter, obs=['charge'], group_by=['conf_params.J'])
        elif args.excited_mixture_errors:
            energy_file = plotting.plot_expectation_vs_parameter_filtered(results_list, output_dir, 'p_excited_mixture_error', filter, obs=['bobs_energy_n2'], group_by=['conf_params.J'])
            charge_file = plotting.plot_expectation_vs_parameter_filtered(results_list, output_dir, 'p_excited_mixture_error', filter, obs=['charge'], group_by=['conf_params.J'])
        elif args.excited_superposition_errors:
            energy_file = plotting.plot_expectation_vs_parameter_filtered(results_list, output_dir, 'p_excited_superposition_error', filter, obs=['bobs_energy_n2'], group_by=['conf_params.J'])
            charge_file = plotting.plot_expectation_vs_parameter_filtered(results_list, output_dir, 'p_excited_superposition_error', filter, obs=['charge'], group_by=['conf_params.J'])

        if args.both_alice_values:
            energy_file = plotting.plot_expectation_vs_parameter_filtered(results_list, output_dir, 'J', filter, obs=['bobs_energy_n2'], group_by=['conf_params.xor_alice_res'])
            charge_file = plotting.plot_expectation_vs_parameter_filtered(results_list, output_dir, 'J', filter, obs=['charge'], group_by=['conf_params.xor_alice_res'])

        if energy_file: plot_filenames.append(energy_file)
        if charge_file: plot_filenames.append(charge_file)

        # file_name = plotting.plot_expectation_vs_parameter_filtered_subplots(results_list, output_dir, 'J', subplot_params=['conf_params.p_dephase'], obs=['bobs_energy_n2'], group_by=['conf_params.xor_alice_res'])
        # file_name = plotting.plot_expectation_vs_parameter_filtered_subplots(results_list, output_dir, 'J', subplot_params=['conf_params.p_dephase'], obs=['charge'], group_by=['conf_params.xor_alice_res'])

    else:
        filter = {}
        file_name = plotting.plot_expectation_vs_parameter_filtered(results_list, output_dir, 'J', filter, obs=['charge_n'], group_by=['conf_params.xor_alice_res'])
        if file_name: plot_filenames.append(file_name)

        file_name = plotting.plot_expectation_vs_parameter_filtered(results_list, output_dir, 'J', filter, obs=['E_B_n_alicex'], group_by=['conf_params.xor_alice_res'])
        if file_name: plot_filenames.append(file_name)
        file_name = plotting.plot_expectation_vs_parameter_filtered(results_list, output_dir, 'J', filter, obs=['E_B_n_alicey'], group_by=['conf_params.xor_alice_res'])
        if file_name: plot_filenames.append(file_name)

    # filter = {'conf_params.h': 1.0, 'conf_params.J': 1.0}
    # file_name = plotting.plot_expectation_vs_parameter_filtered(results_list, output_dir, 'p_dephase')
    # file_name = plotting.plot_expectation_vs_parameter_filtered_subplots(results_list, output_dir, 'p_dephase')

    # files = plotting.plot_counts_hist()
    # plot_filenames.extend(files)

    # file_name = plotting.plot_heatmap(results_list, output_dir)
    # plot_filenames.append(file_name)

    reporting.generate_report(results_list, plot_filenames, output_dir, [])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Quantum Teleportation Simulation")

    parser.add_argument('--all-hJ', action='store_true', help="Run all coupling pairs configurations")
    parser.add_argument('--all-J-for-h', action='store_true', help="Run all J configurations for a specific h value")
    parser.add_argument('--all-dephase', action='store_true', help="Run all p_dephase configurations")
    parser.add_argument('--all-theta', action='store_true', help="Run all theta configurations")
    parser.add_argument('--both-alice-values', action='store_true', help="Run both cases where Alice sends the right or wrong bit to Bob")
    parser.add_argument('--run-analytical', action='store_true', help="Run in analytical calculations mode instead of numerical")
    parser.add_argument('-N', type=int, default=2, help="Choose value for N - the number of sites in chain")

    error_group = parser.add_mutually_exclusive_group(required=False)

    error_group.add_argument('--classical-errors', action='store_true', help="Run classical error simulation")
    error_group.add_argument('--depolarization-errors', action='store_true', help="Run depolarization error simulation")
    error_group.add_argument('--bit-flip-errors', action='store_true', help="Run bit-flip error simulation")
    error_group.add_argument('--alice-phase-flip-errors', action='store_true', help="Run phase-flip error simulation on Alice's site")
    error_group.add_argument('--bob-phase-flip-errors', action='store_true', help="Run phase-flip error simulation on Bob's site")
    error_group.add_argument('--excited-mixture-errors', action='store_true', help="Run mixture with excited states error simulation")
    error_group.add_argument('--excited-superposition-errors', action='store_true', help="Run superposition with excited states error simulation")

    args = parser.parse_args()

    if args.run_analytical and args.N != 2:
        raise ValueError("Only N=2 is supported for analytical simulations. Remove `--run-analytical` for other values.")

    # --- Configuration Loading ---
    confs = [Conf(args.N)]

    if confs[0].run_all or confs[0].run_sampler:
        print("Initializing QiskitRuntimeService()")
        service = QiskitRuntimeService()
    else:
        service = None

    if args.all_hJ:
        confs = [conf for c in confs for conf in Conf.generate_hJ_combinations(c)]
    elif args.all_J_for_h:
        confs = [conf for c in confs for conf in Conf.generate_J_for_h(c)]

    if args.all_dephase:
        confs = [conf for c in confs for conf in Conf.generate_p_dephase_values(c)]

    if args.all_theta:
        confs = [conf for c in confs for conf in Conf.generate_thetas(c)]

    if args.both_alice_values:
        confs = [conf for c in confs for conf in Conf.generate_alice_xor(c)]

    if args.classical_errors:
        confs = [conf for c in confs for conf in Conf.generate_classical_error(c)]

    if args.depolarization_errors:
        confs = [conf for c in confs for conf in Conf.generate_depolarization_error(c)]

    if args.bit_flip_errors:
        confs = [conf for c in confs for conf in Conf.generate_bitflip_error(c)]

    if args.alice_phase_flip_errors:
        confs = [conf for c in confs for conf in Conf.generate_alice_phase_flip_error(c)]

    if args.bob_phase_flip_errors:
        confs = [conf for c in confs for conf in Conf.generate_bob_phase_flip_error(c)]

    if args.excited_mixture_errors:
        confs = [conf for c in confs for conf in Conf.generate_excited_mixture_error(c)]

    if args.excited_superposition_errors:
        confs = [conf for c in confs for conf in Conf.generate_excited_superposition_error(c)]


    print(f"Generated {len(confs)} configurations to run.")
    print_run_plan(confs) # Display the plan based on the configurations list
    input("Press Enter to continue...") # Optional confirmation step

    # --- Observable Setup ---
    observable_factory = ObservableFactory()

    # --- Execution Loop ---
    # Runner initialization logic can be complex depending on backend/noise model sharing.
    # This simple version re-initializes if backend or primary noise param (p_dephase) changes.
    current_runner = None

    for i, conf in enumerate(confs):
        print(f"\n--- Running Configuration {i+1}/{len(confs)} ---")

        tfim = MyCalculatorTFIM(conf.N, conf.J, conf.h) if args.run_analytical else NumericalTFIM(conf.N, conf.J, conf.h)

        tfim.calc_all()
        tfim.apply_errors(conf)

        # Create/get observables for this config (needed for runner)
        # Note: Factory creates *all* observables, runner uses the list of simulatable ones
        simulatable_obs_list = observable_factory.create_observables(conf, tfim)

        # Initialize Runner (or re-init if backend/noise changes significantly)
        # Pass only the list of observables to simulate
        runner = Runner(simulatable_obs_list, service=service)
        # Initialize backend, noise model etc. for this specific conf
        runner.init_run_level(conf, conf.backend)

        # Execute each observable for the current configuration
        for obs in simulatable_obs_list:
             runner.execute_observable(obs, conf, res)

        print(f"\n--- Finished Configuration {i+1}/{len(confs)} ---")

    # --- Post-Processing ---
    print("\n--- Post-Processing Results ---")
    res.process_results() # Calculate metrics, derive observables

    # --- Save Processed Results ---
    res.save_results("processed_results.json")

    # --- Analysis & Reporting ---
    print("\n--- Generating Plots and Report ---")
    # Load results back if needed (e.g., if running analysis separately)
    # res.load_results("processed_results.json")

    report_and_plot(res, args)
    print("\n--- Simulation and Analysis Complete ---")
