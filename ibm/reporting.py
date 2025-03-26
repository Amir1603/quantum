import os
from collections import defaultdict
import operator
from functools import reduce

def _get_nested_value(data_dict, path_str):
    """Helper function reused from plotting.py (consider moving to a utils file)"""
    try:
        return reduce(operator.getitem, path_str.split('.'), data_dict)
    except (KeyError, TypeError, IndexError):
        return None

def _format_value(value, precision=4):
    """Formats numbers for the table, handling None."""
    if value is None:
        return "N/A"
    try:
        # Format as float with specified precision
        return f"{float(value):.{precision}f}"
    except (ValueError, TypeError):
        # Return as string if conversion fails
        return str(value)


def generate_html_report(results_list, plot_filenames, output_dir, report_filename="report.html",
                         table_observables=None, table_configs=None):
    """
    Generates an HTML report summarizing results, embedding plots, and adding data tables.

    Args:
        results_list (list): List of RunResult objects (or dicts).
        plot_filenames (list): List of paths to generated plot files.
        output_dir (str): Directory to save the report.
        report_filename (str, optional): Name of the HTML report file. Defaults to "report.html".
        table_observables (list, optional): List of observable names (str) to include in the tables. If None, attempts to include all non-derived.
        table_configs (list, optional): List of dicts specifying configurations to include in tables.
                                       Example: [{'noise_params.p_dephase': 0.0}] includes all results with p_dephase=0.
                                       If None, includes all results matching table_observables.
    """

    filepath = os.path.join(output_dir, report_filename)

    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Quantum Simulation Report</title>
        <style>
            body { font-family: sans-serif; margin: 20px; }
            h1, h2, h3 { color: #333; }
            img { max-width: 800px; height: auto; border: 1px solid #ddd; margin-bottom: 20px; display: block;}
            table { border-collapse: collapse; margin-bottom: 20px; width: auto; }
            th, td { border: 1px solid #ccc; padding: 8px; text-align: right; }
            th { background-color: #f2f2f2; text-align: center; }
            /* Align first column (Observable names) left */
            td:first-child { text-align: left; }
            pre { background-color: #f8f8f8; border: 1px solid #ddd; padding: 10px; white-space: pre-wrap; word-wrap: break-word; }
            .config-table { margin-top: 15px; }
        </style>
    </head>
    <body>
        <h1>Quantum Simulation Report</h1>
    """

    # --- Summary ---
    html_content += "<h2>Summary</h2>"
    html_content += f"<p>Total results processed: {len(results_list)}</p>"
    # Add more summary info if desired (e.g., unique configurations run)

    # --- Data Tables (Request 3) ---
    html_content += "<h2>Data Tables</h2>"
    if not results_list:
        html_content += "<p>No results available to generate tables.</p>"
    else:
        # Determine which observables to include in tables
        obs_to_include = set()
        if table_observables:
            obs_to_include = set(table_observables)
        else:
            # Default: Include non-derived observables if specific list not given
            obs_to_include = {res.get('observable_name') for res in results_list if res.get('observable_name') and not res.get('is_derived')}

        # Define configurations (filters) for which to generate tables
        configs_to_display = []
        if table_configs:
            configs_to_display = table_configs
        else:
            # Default: If no configs specified, create one table for p_dephase=0 if present,
            # otherwise just one table for all configurations.
            has_p_dephase_zero = any(_get_nested_value(res, 'noise_params.p_dephase') == 0.0 for res in results_list)
            if has_p_dephase_zero:
                configs_to_display.append({'noise_params.p_dephase': 0.0})
            else:
                # Empty dict means no specific filter, show all data matching obs_to_include
                configs_to_display.append({})

        # Generate tables for each specified configuration filter
        for i, config_filter in enumerate(configs_to_display):
            filter_desc = "All Configurations"
            if config_filter:
                 # Create a readable description of the filter
                 filter_desc = ", ".join([f"{k.split('.')[-1]}={v}" for k, v in config_filter.items()])
            html_content += f"<h3>Table {i+1}: Expectation Values ({filter_desc})</h3>"

            # Filter results for this specific table based on config_filter
            table_data = []
            for res_data in results_list:
                 # Convert RunResult object to dict if necessary for consistent access
                 if not isinstance(res_data, dict):
                      from dataclasses import asdict
                      try: res_dict = asdict(res_data)
                      except TypeError: continue # Skip if cannot convert
                 else: res_dict = res_data

                 # Check if observable is one we want in the tables
                 if res_dict.get('observable_name') not in obs_to_include: continue

                 # Apply the config filter for this table
                 match = True
                 for f_key, f_val in config_filter.items():
                     val = _get_nested_value(res_dict, f_key)
                     # Handle potential dict comparison (though less likely here)
                     if isinstance(f_val, dict) and isinstance(val, dict):
                         if val != f_val: match = False; break
                     elif val != f_val:
                         match = False; break
                 if not match: continue

                 # If observable and config match, add to data for this table
                 table_data.append(res_dict)

            if not table_data:
                html_content += f"<p>No results found matching the criteria for this table ({filter_desc}).</p>"
                continue

            # --- Generate HTML Table ---
            # Group the filtered data by (h, k) to create columns
            grouped_by_hk = defaultdict(list)
            for res in table_data:
                 h_val = _get_nested_value(res, 'conf_params.h')
                 k_val = _get_nested_value(res, 'conf_params.k')
                 # Use tuple (h, k) as the key
                 hk_key = (h_val, k_val)
                 grouped_by_hk[hk_key].append(res)

            # Sort columns by h, then k for consistent ordering
            # Handle None values in sorting by placing them at the end
            sorted_hk_keys = sorted(grouped_by_hk.keys(), key=lambda x: (x[0] if x[0] is not None else float('inf'), x[1] if x[1] is not None else float('inf')))

            html_content += '<table class="config-table">'
            html_content += "<thead><tr><th>Observable</th>"
            # Add table headers for each (h, k) pair
            for h, k in sorted_hk_keys:
                html_content += f"<th>(h={h}, k={k})<br>Expectation ± SEM</th>"
            html_content += "</tr></thead>"
            html_content += "<tbody>"

            # Determine the union of all observables present across all included (h,k) groups for rows
            all_obs_in_table = sorted(list(set(res['observable_name'] for hk_key in sorted_hk_keys for res in grouped_by_hk[hk_key])))


            # Create table rows for each unique observable found
            for obs_name in all_obs_in_table:
                 html_content += f"<tr><td>{obs_name}</td>"
                 # Fill in values for each (h, k) column for this observable
                 for hk_key in sorted_hk_keys:
                     # Find the result corresponding to this observable and (h,k)
                     found_res = None
                     for res in grouped_by_hk[hk_key]:
                         if res['observable_name'] == obs_name:
                             found_res = res
                             break # Assume only one result per observable per (h,k,filter) combination

                     if found_res:
                         # Format expectation value and SEM
                         exp_val_str = _format_value(found_res.get('expectation_value'))
                         sem_str = _format_value(found_res.get('sem'))
                         html_content += f"<td>{exp_val_str} ± {sem_str}</td>"
                     else:
                         # Add placeholder if no result was found for this cell
                         html_content += "<td>N/A</td>"
                 html_content += "</tr>" # End observable row

            html_content += "</tbody></table>" # End table


    # --- Plots ---
    html_content += "<h2>Plots</h2>"
    if plot_filenames:
        # Sort filenames for consistent order (optional but good practice)
        plot_filenames.sort()
        for plot_file in plot_filenames:
             # Use relative path for embedding in HTML assuming report and plots are in same dir
             relative_plot_path = os.path.basename(plot_file)
             # Create a slightly nicer title from filename for the heading
             plot_title = os.path.splitext(relative_plot_path)[0].replace("_", " ").replace(" vs ", " vs ").replace(" by ", " by ").title()
             html_content += f'<h3>{plot_title}</h3>\n'
             # Embed the image
             html_content += f'<img src="{relative_plot_path}" alt="Plot: {relative_plot_path}"><br>\n'
    else:
        html_content += "<p>No plots were generated or provided.</p>"


    # --- Raw Results Data (Optional JSON dump - commented out by default) ---
    # html_content += "<h2>Raw Processed Data (JSON)</h2>"
    # try:
    #     # Ensure data is serializable (RunResult objects need conversion, or load from JSON)
    #     # Convert results_list to list of dicts if it contains objects
    #     serializable_results = []
    #     from dataclasses import is_dataclass, asdict
    #     for item in results_list:
    #         if is_dataclass(item) and not isinstance(item, type):
    #             serializable_results.append(asdict(item))
    #         elif isinstance(item, dict):
    #              serializable_results.append(item)
    #         # Add handling for other types if necessary
    #
    #     json_data = json.dumps(serializable_results, indent=4, default=str) # Use default=str for safety
    #     html_content += f"<pre>{json_data}</pre>"
    # except Exception as e:
    #     html_content += f"<p>Error converting results to JSON: {e}</p>"


    html_content += """
    </body>
    </html>
    """

    try:
        # Write the HTML content to file
        with open(filepath, 'w', encoding='utf-8') as f: # Specify encoding for broader compatibility
            f.write(html_content)
        print(f"HTML report saved to {filepath}")
    except Exception as e:
        print(f"Error writing HTML report {filepath}: {e}")
