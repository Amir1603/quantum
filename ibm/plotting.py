import matplotlib.pyplot as plt
from qiskit.visualization import circuit_drawer
import os
from collections import defaultdict
import operator
from functools import reduce
import numpy as np
import pandas as pd


def _get_nested_value(data_dict, path_str):
    """Helper to get value from nested dict using dot notation path."""
    try:
        return reduce(operator.getitem, path_str.split('.'), data_dict)
    except (KeyError, TypeError, IndexError):
        return None

def plot_expectation_vs_parameter(results_list, x_param_path, y_param_path, output_dir,
                                error_param_path=None, group_by=None, filter_criteria=None,
                                observables_to_plot=None,
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
        observables_to_plot (list, optional): List of observable names (strings) to include in the plot. If None, plots all.
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

        # Filter by observable name if specified
        if observables_to_plot and result_dict.get('observable_name') not in observables_to_plot:
            continue

        # Apply filter_criteria
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
                # Include observable name if not grouping by it explicitly
                group_key_parts.append(f"{_get_nested_value(result_dict, 'observable_name')}: {group_param.split('.')[-1]}={group_val}" if 'observable_name' not in group_by else f"{group_val}")
        else:
             # Default group by observable name if no group_by specified
             group_key_parts.append(result_dict.get('observable_name', 'Unknown Obs'))
        group_key = ", ".join(group_key_parts) if group_key_parts else "All Data"

        # Get x, y, error values
        x_val = _get_nested_value(result_dict, x_param_path)
        y_val = _get_nested_value(result_dict, y_param_path)
        e_val = _get_nested_value(result_dict, error_param_path) if error_param_path else None

        if x_val is not None and y_val is not None:
            grouped_data[group_key]['x'].append(x_val)
            grouped_data[group_key]['y'].append(y_val)
            if e_val is not None:
                 # Ensure error list exists and append
                 if 'error' not in grouped_data[group_key]:
                      # Pad if adding error mid-group (pad with zeros for existing points)
                      grouped_data[group_key]['error'] = [0.0] * (len(grouped_data[group_key]['x']) -1)
                 grouped_data[group_key]['error'].append(e_val)
            elif 'error' in grouped_data[group_key]: # Pad if error exists but current point doesn't have one
                 grouped_data[group_key]['error'].append(0.0)


    if not grouped_data:
        print(f"Warning: No data matched the criteria for plot '{title_prefix}'.")
        return None

    # Create plot
    fig, ax = plt.subplots(figsize=(10, 6))
    title = f"{title_prefix} vs {x_param_path.split('.')[-1]}"
    filter_strs = []
    if filter_criteria:
         filter_strs.append(", ".join([f"{k.split('.')[-1]}={v}" for k, v in filter_criteria.items()]))
    if observables_to_plot:
         filter_strs.append(f"Obs={','.join(observables_to_plot)}")
    if filter_strs:
        title += f"\n(Filtered by: {'; '.join(filter_strs)})"

    ax.set_title(title)
    ax.set_xlabel(x_param_path.split('.')[-1])
    ax.set_ylabel(y_param_path.split('.')[-1])

    for group_label, data in grouped_data.items():
        # Ensure all lists have same length before zipping, pad error if needed
        max_len = len(data['x'])
        err_data = data.get('error', [])
        if len(err_data) < max_len:
            err_data.extend([0.0] * (max_len - len(err_data)))

        # Sort data points by x value for consistent plotting
        points = sorted(zip(data['x'], data['y'], err_data))
        x_sorted, y_sorted, err_sorted = zip(*points)

        if data.get('error'):
            ax.errorbar(x_sorted, y_sorted, yerr=err_sorted, label=group_label, marker='o', linestyle='-', capsize=3)
        else:
            ax.plot(x_sorted, y_sorted, label=group_label, marker='o', linestyle='-')

    ax.legend()
    ax.grid(True)
    plt.tight_layout()

    # Save plot
    filename_parts = [filename_prefix, "vs", x_param_path.replace('.', '_')]
    if observables_to_plot:
        filename_parts.append("_".join(observables_to_plot))
    filename = f"{'_'.join(filename_parts)}.png"
    filepath = os.path.join(output_dir, filename)
    try:
        plt.savefig(filepath)
        plt.close(fig) # Close figure to free memory
        return filepath
    except Exception as e:
        print(f"Error saving plot {filepath}: {e}")
        plt.close(fig)
        return None


def plot_expectation_vs_parameter_subplots(results_list, x_param_path, y_param_path, subplot_params, output_dir,
                                          error_param_path=None, line_group_by=None, filter_criteria=None,
                                          observables_to_plot=None,
                                          filename_prefix="subplot", title_prefix="Plot"):
    """
    Generates a figure with subplots based on specified parameter values. Plots expectation value vs. another parameter.

    Args:
        results_list (list): List of RunResult objects (or dicts).
        x_param_path (str): Dot notation path for the x-axis (e.g., 'noise_params.p_dephase').
        y_param_path (str): Dot notation path for the y-axis (e.g., 'expectation_value').
        subplot_params (list): List of parameter paths used to create subplots (e.g., ['conf_params.h', 'conf_params.k']).
        output_dir (str): Directory to save the plot.
        error_param_path (str, optional): Dot notation path for error bars (e.g., 'sem').
        line_group_by (list, optional): Parameter paths to group lines within each subplot (e.g., ['observable_name']).
        filter_criteria (dict, optional): Dictionary for initial filtering of results.
        observables_to_plot (list, optional): List of observable names to include. If None, plots all.
        filename_prefix (str, optional): Prefix for the output filename.
        title_prefix (str, optional): Prefix for the main figure title.

    Returns:
        str: Path to the saved plot file, or None if no data plotted.
    """
    if not results_list:
        print("Warning: No results provided for subplotting.")
        return None

    # --- Data Filtering and Grouping ---
    filtered_results = []
    for result_data in results_list:
        if not isinstance(result_data, dict):
            from dataclasses import asdict
            try: result_dict = asdict(result_data)
            except TypeError: continue
        else: result_dict = result_data

        # Filter by observable name
        if observables_to_plot and result_dict.get('observable_name') not in observables_to_plot: continue

        # Apply general filter_criteria
        if filter_criteria:
            match = True
            for f_key, f_val in filter_criteria.items():
                val = _get_nested_value(result_dict, f_key)
                if isinstance(f_val, dict) and isinstance(val, dict):
                    if val != f_val: match = False; break
                elif val != f_val: match = False; break
            if not match: continue

        filtered_results.append(result_dict)

    if not filtered_results:
        print("Warning: No results matched initial filter criteria for subplots.")
        return None

    # Identify unique subplot groups
    subplot_groups = defaultdict(list)
    for res in filtered_results:
        subplot_key_parts = []
        valid_key = True
        for param in subplot_params:
            val = _get_nested_value(res, param)
            if val is None:
                valid_key = False; break
            subplot_key_parts.append(f"{param.split('.')[-1]}={val}")
        if valid_key:
            subplot_key = ", ".join(subplot_key_parts)
            subplot_groups[subplot_key].append(res)

    if not subplot_groups:
        print("Warning: Could not group data for subplots.")
        return None

    # --- Plotting Setup ---
    n_subplots = len(subplot_groups)
    # Simple grid layout - adjust as needed (e.g., aim for roughly square)
    ncols = int(np.ceil(np.sqrt(n_subplots)))
    nrows = int(np.ceil(n_subplots / ncols))

    fig, axes = plt.subplots(nrows, ncols, figsize=(ncols * 5, nrows * 4), squeeze=False) # Ensure axes is always 2D
    fig.suptitle(f"{title_prefix} vs {x_param_path.split('.')[-1]} (Subplots by {', '.join([p.split('.')[-1] for p in subplot_params])})", fontsize=14)
    ax_flat = axes.flatten()

    # --- Plotting Each Subplot ---
    plot_idx = 0
    for subplot_key, subplot_data_list in subplot_groups.items():
        ax = ax_flat[plot_idx]
        ax.set_title(subplot_key)
        ax.set_xlabel(x_param_path.split('.')[-1])
        ax.set_ylabel(y_param_path.split('.')[-1])
        ax.grid(True)

        # Group data within the subplot (for lines)
        lines_data = defaultdict(lambda: defaultdict(list))
        for res in subplot_data_list:
            line_key_parts = []
            if line_group_by:
                for param in line_group_by:
                     val = _get_nested_value(res, param)
                     # Use just the value for the legend label if grouping by it
                     line_key_parts.append(f"{val}")
            else:
                 # Default to grouping by observable if not specified
                 line_key_parts.append(res.get('observable_name', 'Unknown'))
            line_key = ", ".join(line_key_parts)

            x_val = _get_nested_value(res, x_param_path)
            y_val = _get_nested_value(res, y_param_path)
            e_val = _get_nested_value(res, error_param_path) if error_param_path else None

            if x_val is not None and y_val is not None:
                lines_data[line_key]['x'].append(x_val)
                lines_data[line_key]['y'].append(y_val)
                if e_val is not None:
                    if 'error' not in lines_data[line_key]: lines_data[line_key]['error'] = [0.0] * (len(lines_data[line_key]['x'])-1)
                    lines_data[line_key]['error'].append(e_val)
                elif 'error' in lines_data[line_key]: lines_data[line_key]['error'].append(0.0)

        if not lines_data:
            ax.text(0.5, 0.5, "No data for this subplot", ha='center', va='center')
        else:
            for line_label, data in lines_data.items():
                max_len = len(data['x'])
                err_data = data.get('error', [])
                if len(err_data) < max_len: err_data.extend([0.0] * (max_len - len(err_data)))

                points = sorted(zip(data['x'], data['y'], err_data))
                x_sorted, y_sorted, err_sorted = zip(*points)

                if data.get('error'):
                    ax.errorbar(x_sorted, y_sorted, yerr=err_sorted, label=line_label, marker='.', linestyle='-', capsize=3)
                else:
                    ax.plot(x_sorted, y_sorted, label=line_label, marker='.', linestyle='-')
            ax.legend()
        plot_idx += 1

    # Hide unused axes
    for i in range(plot_idx, len(ax_flat)):
        ax_flat[i].set_visible(False)

    plt.tight_layout(rect=[0, 0.03, 1, 0.95]) # Adjust layout to prevent title overlap

    # --- Save Plot ---
    filename = f"{filename_prefix}_vs_{x_param_path.replace('.', '_')}_by_{'_'.join([p.replace('.', '_') for p in subplot_params])}.png"
    filepath = os.path.join(output_dir, filename)
    try:
        plt.savefig(filepath)
        plt.close(fig)
        return filepath
    except Exception as e:
        print(f"Error saving subplot figure {filepath}: {e}")
        plt.close(fig)
        return None


def plot_counts_histogram(counts, observable_name, output_dir, filename_prefix="hist", title_info=""):
    """
    Generates a histogram of measurement counts.

    Args:
        counts (dict): Dictionary of {'bitstring': count}.
        observable_name (str): Name of the observable for titles/filenames.
        output_dir (str): Directory to save the plot.
        filename_prefix (str, optional): Prefix for the output plot filename. Defaults to "hist".
        title_info(str, optional): Additional info for the title (e.g., h, k, p_dephase).

    Returns:
        str: The path to the saved plot file, or None if counts are empty.
    """
    if not counts:
        print(f"Warning: No counts provided for histogram of {observable_name}.")
        return None

    bitstrings = list(counts.keys())
    count_values = list(counts.values())

    # Create plot
    fig, ax = plt.subplots(figsize=(10, 6))
    title = f"Counts Histogram for {observable_name}"
    if title_info:
        title += f"\n({title_info})"
    ax.set_title(title)
    ax.set_xlabel("Measurement Outcome (Bitstring)")
    ax.set_ylabel("Counts")

    # Use bar chart for discrete outcomes
    x_pos = np.arange(len(bitstrings))
    ax.bar(x_pos, count_values, align='center', alpha=0.7)
    ax.set_xticks(x_pos)
    ax.set_xticklabels(bitstrings, rotation=45, ha='right') # Rotate labels if many outcomes
    ax.grid(True, axis='y')
    plt.tight_layout()

    # Save plot
    # Make filename safe
    safe_obs_name = "".join(c if c.isalnum() else "_" for c in observable_name)
    safe_title_info = "".join(c if c.isalnum() else "_" for c in title_info).strip('_')
    filename = f"{filename_prefix}_{safe_obs_name}{'_' + safe_title_info if safe_title_info else ''}.png"
    filepath = os.path.join(output_dir, filename)
    try:
        plt.savefig(filepath)
        plt.close(fig) # Close figure to free memory
        return filepath
    except Exception as e:
        print(f"Error saving histogram {filepath}: {e}")
        plt.close(fig)
        return None


def plot_heatmap_vs_hk(results_list, h_param_path, k_param_path, z_param_path, output_dir,
                       filter_criteria=None,
                       observable_to_plot=None, # Use string for single observable heatmaps
                       filename_prefix="heatmap", title_prefix="Heatmap",
                       cmap='viridis', # Colormap
                       z_label=None # Optional custom label for the colorbar
                       ):
    """
    Generates a heatmap of a z-parameter vs h and k parameters.

    Args:
        results_list (list): List of RunResult objects (or dicts).
        h_param_path (str): Dot notation path to the h parameter (y-axis).
        k_param_path (str): Dot notation path to the k parameter (x-axis).
        z_param_path (str): Dot notation path to the parameter for the color intensity (z-axis).
        output_dir (str): Directory to save the plot.
        filter_criteria (dict, optional): Dictionary for initial filtering of results. Defaults to None.
        observable_to_plot (str, optional): Specific observable name (string) to filter by. Defaults to None.
        filename_prefix (str, optional): Prefix for the output plot filename. Defaults to "heatmap".
        title_prefix (str, optional): Prefix for the plot title. Defaults to "Heatmap".
        cmap (str, optional): Matplotlib colormap name. Defaults to 'viridis'.
        z_label (str, optional): Custom label for the colorbar. Defaults to z_param_path name.


    Returns:
        str: The path to the saved plot file, or None if no data plotted.
    """
    if not results_list:
        print("Warning: No results provided for heatmap plotting.")
        return None

    # --- Data Filtering and Extraction ---
    data_for_df = []
    for result_data in results_list:
        if not isinstance(result_data, dict):
            from dataclasses import asdict
            try: result_dict = asdict(result_data)
            except TypeError: continue
        else: result_dict = result_data

        # Filter by observable name if specified
        # Note: Heatmaps usually make sense for a single observable type at a time
        obs_name = result_dict.get('observable_name', 'Unknown')
        if observable_to_plot and obs_name != observable_to_plot:
             # Allow partial match if observable name includes theta etc.
             if not observable_to_plot in obs_name:
                  continue

        # Apply general filter_criteria
        match = True
        if filter_criteria:
            for f_key, f_val in filter_criteria.items():
                val = _get_nested_value(result_dict, f_key)
                if isinstance(f_val, dict) and isinstance(val, dict):
                    if val != f_val: match = False; break
                # Special check for apply_protocol (might be bool or derived from name)
                elif f_key == 'apply_protocol' and isinstance(f_val, bool):
                     derived_ap = 'no_protocol' not in obs_name # Infer from name if direct key absent
                     actual_ap = _get_nested_value(result_dict, 'apply_protocol')
                     if actual_ap is None: actual_ap = derived_ap # Fallback
                     if actual_ap != f_val: match=False; break
                elif val != f_val:
                     match = False; break
            if not match: continue

        # Extract h, k, z values
        h_val = _get_nested_value(result_dict, h_param_path)
        k_val = _get_nested_value(result_dict, k_param_path)
        z_val = _get_nested_value(result_dict, z_param_path)

        if h_val is not None and k_val is not None and z_val is not None:
            data_for_df.append({'h': h_val, 'k': k_val, 'z': z_val})

    if not data_for_df:
        print(f"Warning: No data matched the criteria for heatmap '{title_prefix}'. Filter: {filter_criteria}, Observable: {observable_to_plot}")
        return None

    # --- Grid Preparation using Pandas ---
    df = pd.DataFrame(data_for_df)

    # Handle potential duplicate (h, k) pairs by averaging z value
    df_grouped = df.groupby(['h', 'k']).mean().reset_index()

    try:
        # Pivot the data to create a grid: index=h, columns=k, values=z
        heatmap_data = df_grouped.pivot(index='h', columns='k', values='z')
    except Exception as e:
        print(f"Error pivoting data for heatmap. Ensure h/k values form a grid. Error: {e}")
        # Try to provide more debug info
        print("Unique h values:", sorted(df_grouped['h'].unique()))
        print("Unique k values:", sorted(df_grouped['k'].unique()))
        print("Data count per (h,k) pair (should be 1 after grouping):")
        print(df.groupby(['h', 'k']).size())
        return None


    # Get sorted h and k values for axis labels/extent
    h_coords = sorted(heatmap_data.index)
    k_coords = sorted(heatmap_data.columns)

    # --- Plotting ---
    fig, ax = plt.subplots(figsize=(8, 6.5)) # Adjust size as needed

    # Use imshow. extent defines the boundaries [left, right, bottom, top]
    # Adjust extent slightly to center pixels over coordinates if needed, or use pcolormesh
    k_min, k_max = min(k_coords), max(k_coords)
    h_min, h_max = min(h_coords), max(h_coords)
    # imshow extent should align with the data grid boundaries
    # If k_coords are centers, boundaries are midpoints. Similar for h.
    # For simplicity if grid is uniform:
    dk = (k_max - k_min) / (len(k_coords) - 1) if len(k_coords) > 1 else 0
    dh = (h_max - h_min) / (len(h_coords) - 1) if len(h_coords) > 1 else 0
    extent = [k_min - dk/2, k_max + dk/2, h_min - dh/2, h_max + dh/2]


    # Display the heatmap data. Origin='lower' puts h=min at bottom.
    im = ax.imshow(heatmap_data.values, interpolation='nearest', origin='lower',
                   aspect='auto', extent=extent, cmap=cmap)

    # Add colorbar
    cbar_label = z_label if z_label else z_param_path.split('.')[-1]
    cbar = fig.colorbar(im, ax=ax, label=cbar_label)

    # Set title and labels
    title = f"{title_prefix}: {cbar_label}"
    if observable_to_plot:
        title += f" for {observable_to_plot}"
    filter_strs = []
    if filter_criteria:
        # Nicer filter display
        for k, v in filter_criteria.items():
             # Handle boolean apply_protocol display
             if k == 'apply_protocol':
                  filter_strs.append("Protocol ON" if v else "Protocol OFF")
             else:
                  filter_strs.append(f"{k.split('.')[-1]}={v}")
    if filter_strs:
        title += f"\n(Filtered by: {'; '.join(filter_strs)})"
    ax.set_title(title)
    ax.set_xlabel(k_param_path.split('.')[-1] + " (k)") # Match Fig 8 axes
    ax.set_ylabel(h_param_path.split('.')[-1] + " (h)")

    # Optional: Set ticks explicitly if needed, otherwise imshow uses extent
    # ax.set_xticks(...)
    # ax.set_yticks(...)

    plt.tight_layout()

    # --- Save Plot ---
    filename_parts = [filename_prefix, z_param_path.replace('.', '_'), 'vs']
    filename_parts.append(f"{k_param_path.replace('.', '_')}_{h_param_path.replace('.', '_')}")
    if observable_to_plot:
        # Make observable name filename-safe
        safe_obs_name = "".join(c if c.isalnum() else "_" for c in observable_to_plot).strip('_')
        filename_parts.append(safe_obs_name)
    # Add simple filter info to filename
    if filter_criteria:
         if filter_criteria.get('apply_protocol') == True:
             filename_parts.append("protocol_on")
         elif filter_criteria.get('apply_protocol') == False:
             filename_parts.append("protocol_off")

    filename = f"{'_'.join(filename_parts)}.png"
    filepath = os.path.join(output_dir, filename)

    try:
        plt.savefig(filepath)
        plt.close(fig) # Close figure to free memory
        print(f"Heatmap saved to: {filepath}")
        return filepath
    except Exception as e:
        print(f"Error saving heatmap {filepath}: {e}")
        plt.close(fig)
        return None


def draw_circuit(qc, output_dir, conf):
    qcs_dir = os.path.join(output_dir, 'qcs', f'h_{conf.h}_k_{conf.k}')
    os.makedirs(qcs_dir, exist_ok=True)
    circuit_drawer(qc, output='mpl', filename=os.path.join(qcs_dir, f'{qc.name}.png'))

# --- Add other plotting functions as needed ---
# def plot_correlation_matrix(...)