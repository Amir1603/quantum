import argparse
import os
from datetime import datetime
from conf import Conf
from Observables import ObservableFactory
from runner import Runner
from results import Results
import plotting
import reporting


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


def _get_nested_value(data_dict, path_str):
    """Helper to get value from nested dict/object using dot notation path."""
    # Handle if data_dict is an object (like RunResult or Conf)
    current_val = data_dict
    try:
        for key in path_str.split('.'):
            if isinstance(current_val, dict):
                current_val = current_val[key]
            else:
                # Use getattr for objects
                current_val = getattr(current_val, key)
        return current_val
    except (KeyError, AttributeError, TypeError, IndexError):
         # Return None if any part of the path fails
         return None


def report_and_plot(results_obj: Results):
    """Generates plots and the final HTML report."""
    results_list = results_obj.processed_results # Use the processed results list
    output_dir = results_obj.output_dir
    plot_filenames = [] # Collect paths to generated plots for the report

    if not results_list:
        print("No processed results to plot or report.")
        return

    # --- Plotting ---

    # Expectation vs p_dephase (Filtered Observables)
    try:
        # Define observables of interest for this plot
        selected_obs_plot = ['charge']#, 'current', 'total_energy']
        # Example: Filter for a specific h, k combination
        filter_criteria_plot1 = {'conf_params.h': 1.0, 'conf_params.k': 1.0}

        plot_exp_vs_p_filt = plotting.plot_expectation_vs_parameter(
            results_list=results_list,
            x_param_path='conf_params.theta', # Use correct path for p_dephase from Conf
            y_param_path='expectation_value',
            error_param_path='sem',
            output_dir=output_dir,
            filename_prefix="exp_vs_theta",
            title_prefix=f"Expectation Value vs theta (h={filter_criteria_plot1['conf_params.h']}, k={filter_criteria_plot1['conf_params.k']})",
            group_by=['observable_name'], # Separate lines for each selected observable
            filter_criteria=filter_criteria_plot1,
            observables_to_plot=selected_obs_plot # Apply observable filter
        )
        if plot_exp_vs_p_filt: plot_filenames.append(plot_exp_vs_p_filt)
        print(f"Generated plot (filtered obs): {plot_exp_vs_p_filt}")

    except Exception as e:
        print(f"Error during filtered expectation plot: {e}")

    # # Expectation vs p_dephase (Subplots for different h, k)
    # try:
    #     plot_exp_vs_p_subplot = plotting.plot_expectation_vs_parameter_subplots(
    #          results_list=results_list,
    #          x_param_path='conf_params.p_dephase', # Path to p_dephase
    #          y_param_path='expectation_value',
    #          subplot_params=['conf_params.h', 'conf_params.k'], # Create subplots based on h and k
    #          output_dir=output_dir,
    #          error_param_path='sem',
    #          line_group_by=['observable_name'], # Lines within each subplot correspond to observables
    #          # filter_criteria={}, # Optional: Add global filters if needed, e.g., for specific run types
    #          observables_to_plot=selected_obs_plot, # Filter observables globally for these subplots
    #          filename_prefix="exp_vs_p_dephase_subplots_hk",
    #          title_prefix="Expectation Value vs Dephasing"
    #     )
    #     if plot_exp_vs_p_subplot: plot_filenames.append(plot_exp_vs_p_subplot)
    #     print(f"Generated plot (subplots): {plot_exp_vs_p_subplot}")

    # except Exception as e:
    #     print(f"Error during subplot generation: {e}")

    # # Counts Histograms
    # try:
    #     print("\n--- Generating Example Histograms ---")
    #     hist_count = 0
    #     # Limit the number of histograms generated to avoid too many files
    #     max_hists = 5
    #     for result in results_list:
    #          # Define criteria for which runs to generate histograms
    #          # Example: Generate for 'charge' observable, specific (h, k), and p_dephase = 0
    #          is_target_hist = (
    #              result.observable_name == 'charge' and
    #              _get_nested_value(result, 'conf_params.h') == 1.0 and
    #              _get_nested_value(result, 'conf_params.k') == 1.0 and
    #              _get_nested_value(result, 'conf_params.p_dephase') == 0.0 # Check p_dephase from conf_params
    #          )
    #          # Add more conditions or different examples as needed

    #          # Check if counts data exists and if it matches the target criteria
    #          if is_target_hist and result.counts and hist_count < max_hists:
    #               # Create descriptive info for the title and filename
    #               h_val = _get_nested_value(result, 'conf_params.h')
    #               k_val = _get_nested_value(result, 'conf_params.k')
    #               p_d_val = _get_nested_value(result, 'conf_params.p_dephase')
    #               title_info = f"h={h_val}, k={k_val}, p_d={p_d_val}"

    #               hist_filename = plotting.plot_counts_histogram(
    #                   counts=result.counts,
    #                   observable_name=result.observable_name,
    #                   output_dir=output_dir,
    #                   filename_prefix="hist",
    #                   title_info=title_info
    #               )
    #               if hist_filename:
    #                   plot_filenames.append(hist_filename)
    #                   print(f"Generated histogram: {hist_filename}")
    #                   hist_count += 1 # Increment counter

    #     if hist_count == 0:
    #          print("No target results found matching criteria for example histograms.")

    # except Exception as e:
    #     print(f"Error during histogram generation: {e}")


    plot_heatmap = plotting.plot_heatmap_vs_hk(
        results_list=results_list,
        h_param_path='conf_params.h',
        k_param_path='conf_params.k',
        z_param_path='expectation_value', # Path to the value you want to plot
        output_dir=output_dir,
        observable_to_plot='charge',
        filter_criteria={},
        filename_prefix='heatmap_charge_expval',
        title_prefix='Expectation Value vs (h, k)',
        cmap='viridis',
        z_label='Avg Charge <rho>'
    )
    if plot_heatmap: plot_filenames.append(plot_heatmap)
    print(f"Generated heatmap plot: {plot_heatmap}")


    # --- Generate HTML Report (including tables - Request 3) ---
    try:
        # Define which observables to include in the tables
        # Include protocol and no-protocol versions, plus energy terms if desired
        table_obs_report = ['charge', 'current', 'charge_no_protocol', 'current_no_protocol', 'total_energy']
        # Define the configurations (filters) for the tables
        table_configs_report = [
            {'conf_params.p_dephase': 0.0},
        ]

        reporting.generate_html_report(
            results_list=results_list, # Pass the processed list of RunResult objects/dicts
            plot_filenames=plot_filenames, # Pass paths to all generated plots
            output_dir=output_dir,
            report_filename="final_report.html",
            table_observables=table_obs_report, # Specify observables for tables
            table_configs=table_configs_report # Specify configurations/filters for tables
        )
        print(f"Generated HTML report in {output_dir}")

    except Exception as e:
        print(f"Error during HTML reporting: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Quantum Teleportation Simulation")

    # Allow overriding specific Conf parameters via command line
    parser.add_argument('--h-param', type=float, help="Override 'h' parameter in conf.yaml")
    parser.add_argument('--k-param', type=float, help="Override 'k' parameter in conf.yaml")
    parser.add_argument('--total-shots', type=int, help="Override 'total_shots' in conf.yaml") # Use int for shots
    # Allow running all generated configurations instead of just one
    parser.add_argument('--run-all-conf', action='store_true', help="Run all configurations generated by Conf.generate_all_confs()") # Changed to store_true

    args = parser.parse_args()

    # --- Configuration Loading ---
    confs = []
    if args.run_all_conf:
        # Generate multiple configurations based on ranges defined in Conf class
        confs = Conf.generate_all_confs()
        if not confs:
            print("Warning: generate_all_confs() returned no configurations. Check Conf class.")
            exit() # Exit if no configurations are generated
    else:
        # Load a single configuration, potentially overriding from CLI args
        conf = Conf() # Create default Conf instance
        try:
            conf.load() # Load parameters from conf.yaml
            print("Loaded configuration from conf.yaml")
        except FileNotFoundError:
            print("conf.yaml not found, using default Conf parameters.")
        except Exception as e:
            print(f"Error loading conf.yaml: {e}. Using default Conf parameters.")

        # Override specific parameters if provided via command line
        if args.h_param is not None: conf.h = args.h_param
        if args.k_param is not None: conf.k = args.k_param
        if args.total_shots is not None: conf.total_shots = args.total_shots
        confs.append(conf) # Add the single (potentially modified) config to the list

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
        print(conf) # Print current config

        # Create/get observables for this config (needed for runner)
        # Note: Factory creates *all* observables, runner uses the list of simulatable ones
        simulatable_obs_list = observable_factory.create_observables(conf)

        # Initialize Runner (or re-init if backend/noise changes significantly)
        # Pass only the list of observables to simulate
        runner = Runner(simulatable_obs_list)
        # Initialize backend, noise model etc. for this specific conf
        runner.init_run_level(conf, conf.backend)

        # Execute each observable for the current configuration
        for obs in simulatable_obs_list:
             runner.execute_observable(obs, conf, res)

        print(f"--- Finished Configuration {i+1}/{len(confs)} ---")


    # --- Post-Processing ---
    print("\n--- Post-Processing Results ---")
    res.process_results(observable_factory) # Calculate metrics, derive observables

    # --- Save Processed Results ---
    res.save_results("processed_results.json")

    # --- Analysis & Reporting ---
    print("\n--- Generating Plots and Report ---")
    # Load results back if needed (e.g., if running analysis separately)
    # res.load_results("processed_results.json")

    report_and_plot(res)
    print("\n--- Simulation and Analysis Complete ---")
