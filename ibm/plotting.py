import matplotlib.pyplot as plt
import os
from collections import defaultdict
import operator
from functools import reduce


def _get_nested_value(data_dict, path_str):
    """Helper to get value from nested dict using dot notation path."""
    try:
        return reduce(operator.getitem, path_str.split('.'), data_dict)
    except (KeyError, TypeError, IndexError):
        return None

def plot_expectation_vs_parameter(results_list, x_param_path, y_param_path, output_dir,
                                error_param_path=None, group_by=None, filter_criteria=None,
                                filename_prefix="plot", title_prefix="Plot"):
    """
    Generates a plot of one parameter vs another, optionally grouped and filtered.

    Args:
        results_list (list): List of RunResult objects (or dicts).
        x_param_path (str): Dot notation path to the parameter for the x-axis (e.g., 'noise_params.p_dephase').
        y_param_path (str): Dot notation path to the parameter for the y-axis (e.g., 'expectation_value').
        output_dir (str): Directory to save the plot.
        error_param_path (str, optional): Dot notation path to the error bar values (e.g., 'sem'). Defaults to None.
        group_by (list, optional): List of parameter paths to group data by (creating separate lines/markers). Defaults to None.
        filter_criteria (dict, optional): Dictionary where keys are parameter paths and values are required values to include data. Defaults to None.
        filename_prefix (str, optional): Prefix for the output plot filename. Defaults to "plot".
        title_prefix (str, optional): Prefix for the plot title. Defaults to "Plot".

    Returns:
        str: The path to the saved plot file, or None if no data plotted.
    """
    if not results_list:
        print("Warning: No results provided for plotting.")
        return None

    grouped_data = defaultdict(lambda: defaultdict(list))

    # Filter and group data
    for result_data in results_list:
        # Convert RunResult object to dict if necessary
        if not isinstance(result_data, dict):
            from dataclasses import asdict
            try:
                result_dict = asdict(result_data)
            except TypeError:
                print(f"Warning: Could not convert result to dict: {result_data}")
                continue
        else:
            result_dict = result_data

        # Apply filter
        if filter_criteria:
            match = True
            for filter_key, filter_val in filter_criteria.items():
                val = _get_nested_value(result_dict, filter_key)
                # Handle potential dict comparison in noise_params
                if isinstance(filter_val, dict) and isinstance(val, dict):
                    if val != filter_val:
                         match = False
                         break
                elif val != filter_val:
                    match = False
                    break
            if not match:
                continue

        # Get group key
        group_key_parts = []
        if group_by:
            for group_param in group_by:
                group_val = _get_nested_value(result_dict, group_param)
                group_key_parts.append(f"{group_param.split('.')[-1]}={group_val}")
        group_key = ", ".join(group_key_parts) if group_key_parts else "All Data"

        # Get x, y, error values
        x_val = _get_nested_value(result_dict, x_param_path)
        y_val = _get_nested_value(result_dict, y_param_path)
        e_val = _get_nested_value(result_dict, error_param_path) if error_param_path else None

        if x_val is not None and y_val is not None:
            grouped_data[group_key]['x'].append(x_val)
            grouped_data[group_key]['y'].append(y_val)
            if e_val is not None:
                grouped_data[group_key]['error'].append(e_val)
            else:
                 # Ensure error list matches length if some points have errors and others don't
                 if 'error' in grouped_data[group_key]:
                      grouped_data[group_key]['error'].append(0.0)


    if not grouped_data:
        print(f"Warning: No data matched the criteria for plot '{title_prefix}'.")
        return None

    # Create plot
    fig, ax = plt.subplots(figsize=(10, 6))
    title = f"{title_prefix} vs {x_param_path.split('.')[-1]}"
    if filter_criteria:
         filter_str = ", ".join([f"{k.split('.')[-1]}={v}" for k, v in filter_criteria.items()])
         title += f"\n(Filtered by: {filter_str})"
    ax.set_title(title)
    ax.set_xlabel(x_param_path.split('.')[-1])
    ax.set_ylabel(y_param_path.split('.')[-1])

    for group_label, data in grouped_data.items():
        # Sort data points by x value for consistent plotting
        points = sorted(zip(data['x'], data['y'], data.get('error', [0]*len(data['x']))))
        x_sorted, y_sorted, err_sorted = zip(*points)

        if data.get('error'):
            ax.errorbar(x_sorted, y_sorted, yerr=err_sorted, label=group_label, marker='o', linestyle='-', capsize=3)
        else:
            ax.plot(x_sorted, y_sorted, label=group_label, marker='o', linestyle='-')

    ax.legend()
    ax.grid(True)
    plt.tight_layout()

    # Save plot
    filename = f"{filename_prefix}_vs_{x_param_path.replace('.', '_')}.png"
    filepath = os.path.join(output_dir, filename)
    try:
        plt.savefig(filepath)
        plt.close(fig) # Close figure to free memory
        return filepath
    except Exception as e:
        print(f"Error saving plot {filepath}: {e}")
        plt.close(fig)
        return None

# --- Add other plotting functions as needed ---
# def plot_counts_histogram(...)
# def plot_correlation_matrix(...)