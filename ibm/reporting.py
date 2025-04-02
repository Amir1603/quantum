import os
from collections import defaultdict
from dataclasses import asdict, is_dataclass
from utils import get_nested_value


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
    Generates an HTML report summarizing results, embedding plots, and adding data tables
    for expectation values and susceptibilities. (Modified based on user-provided code)

    Args:
        results_list (list): List of RunResult objects (or dicts - code handles both).
        plot_filenames (list): List of paths to generated plot files.
        output_dir (str): Directory to save the report.
        report_filename (str, optional): Name of the HTML report file. Defaults to "report.html".
        table_observables (list, optional): List of observable names (str) to include in the tables. If None, attempts to include all non-derived.
        table_configs (list, optional): List of dicts specifying configurations to include in tables.
                                       Example: [{'noise_params.p_dephase': 0.0}] includes all results with p_dephase=0.
                                       If None, includes all results matching table_observables.
    """

    filepath = os.path.join(output_dir, report_filename)

    # --- Start HTML Content (Identical to your provided code) ---
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Quantum Simulation Report</title>
        <style>
            body { font-family: sans-serif; margin: 20px; }
            h1, h2, h3 { color: #333; }
            h3 { margin-top: 30px; } /* Added margin for better table spacing */
            img { max-width: 800px; height: auto; border: 1px solid #ddd; margin-bottom: 20px; display: block;}
            table { border-collapse: collapse; margin-bottom: 20px; width: auto; }
            th, td { border: 1px solid #ccc; padding: 8px; text-align: right; }
            th { background-color: #f2f2f2; text-align: center; }
            /* Align first column (Observable names) left */
            td:first-child { text-align: left; font-weight: bold; } /* Made observable name bold */
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

    # --- Data Tables ---
    html_content += "<h2>Data Tables</h2>"
    if not results_list:
        html_content += "<p>No results available to generate tables.</p>"
    else:
        # Determine which observables to include in tables
        obs_to_include = set()
        if table_observables:
            obs_to_include = set(table_observables)
        else:
            temp_obs = set()
            for res in results_list:
                 obs_name = None
                 is_derived = False
                 # Handle dict or object access robustly
                 if isinstance(res, dict):
                     obs_name = res.get('observable').name
                     is_derived = res.get('is_derived', False)
                 elif hasattr(res, 'observable'): # Check for attribute
                     obs_name = getattr(res, 'observable').name
                     is_derived = getattr(res, 'is_derived', False)

                 if obs_name and not is_derived:
                     temp_obs.add(obs_name)
            obs_to_include = temp_obs


        # Define configurations
        configs_to_display = []
        if table_configs:
            configs_to_display = table_configs
        else:
            def get_val_safe(item, key):
                 item_dict = item if isinstance(item, dict) else (asdict(item) if is_dataclass(item) and not isinstance(item, type) else {})
                 return get_nested_value(item_dict, key)

            has_p_dephase_zero = any(get_val_safe(res, 'noise_params.p_dephase') == 0.0 for res in results_list)
            if has_p_dephase_zero:
                configs_to_display.append({'noise_params.p_dephase': 0.0})
            else:
                configs_to_display.append({})

        # Generate tables for each specified configuration filter
        for i, config_filter in enumerate(configs_to_display):
            filter_desc = "All Configurations"
            if config_filter:
                 filter_desc = ", ".join([f"{k.split('.')[-1]}={v}" for k, v in config_filter.items()])

            # Filter and Group Data
            table_data = [] # Holds results matching current filter and desired observables
            for res_data in results_list:
                 # Convert potential object to dict
                 if not isinstance(res_data, dict):
                      if is_dataclass(res_data) and not isinstance(res_data, type):
                           try: res_dict = asdict(res_data)
                           except TypeError: continue
                      else: continue
                 else: res_dict = res_data

                 # Check observable
                 if res_dict.get('observable').name not in obs_to_include: continue

                 # Apply config filter
                 match = True
                 for f_key, f_val in config_filter.items():
                     val = get_nested_value(res_dict, f_key)
                     if isinstance(f_val, dict) and isinstance(val, dict):
                         if val != f_val: match = False; break
                     elif val != f_val:
                         match = False; break
                 if not match: continue

                 table_data.append(res_dict)

            if not table_data:
                html_content += f"<h3>Table Set {i+1}: ({filter_desc})</h3>" # Use a set title
                html_content += f"<p>No results found matching the criteria for this table set ({filter_desc}).</p>"
                continue

            # Group by (h, k)
            grouped_by_hk = defaultdict(list)
            for res in table_data:
                 h_val = get_nested_value(res, 'conf_params.h')
                 k_val = get_nested_value(res, 'conf_params.k')
                 hk_key = (h_val, k_val)
                 grouped_by_hk[hk_key].append(res)

            # Sort columns
            sorted_hk_keys = sorted(grouped_by_hk.keys(), key=lambda x: (x[0] if x[0] is not None else float('inf'), x[1] if x[1] is not None else float('inf')))

            # Get unique observables for rows
            all_obs_in_table = sorted(list(set(res['observable'].name for hk_key in sorted_hk_keys for res in grouped_by_hk[hk_key])))


            # --- Generate Expectation Value Table ---
            html_content += f"<h3>Table {i*2+1}: Expectation Values ({filter_desc})</h3>"
            html_content += '<table class="config-table">'
            html_content += "<thead><tr><th>Observable</th>"
            for h, k in sorted_hk_keys:
                html_content += f"<th>(h={h}, k={k})<br>Expectation ± SEM</th>"
            html_content += "</tr></thead>"
            html_content += "<tbody>"
            for obs_name in all_obs_in_table:
                 html_content += f"<tr><td>{obs_name}</td>"
                 for hk_key in sorted_hk_keys:
                     found_res = next((res for res in grouped_by_hk[hk_key] if res['observable'].name == obs_name), None)
                     if found_res:
                         exp_val_str = _format_value(found_res.get('expectation_value'))
                         sem_str = _format_value(found_res.get('sem'))
                         html_content += f"<td>{exp_val_str} ± {sem_str}</td>"
                     else:
                         html_content += "<td>N/A</td>"
                 html_content += "</tr>"
            html_content += "</tbody></table>"


            # --- Generate Susceptibility Table ---
            html_content += f"<h3>Table {i*2+2}: Susceptibility ({filter_desc})</h3>"
            html_content += '<table class="config-table">' # Use the same class
            html_content += "<thead><tr><th>Observable</th>" # Header row start

            # Add table headers for each (h, k) pair for susceptibility
            for h, k in sorted_hk_keys:
                html_content += f"<th>(h={h}, k={k})<br>Susceptibility</th>"
            html_content += "</tr></thead>"
            html_content += "<tbody>"

            # Create table rows using the *same* observables as the expectation table
            for obs_name in all_obs_in_table:
                 html_content += f"<tr><td>{obs_name}</td>" # Observable name cell

                 # Fill in values for each (h, k) column for this observable
                 for hk_key in sorted_hk_keys:
                     # Find the result dictionary corresponding to this observable and (h,k)
                     # Reusing the same 'found_res' logic pattern
                     found_res = next((res for res in grouped_by_hk[hk_key] if res['observable'].name == obs_name), None)

                     if found_res:
                         sus_val = found_res.get('susceptibility')
                         sus_val_str = _format_value(sus_val)

                         # Format the cell content
                         if sus_val_str != "N/A":
                            html_content += f"<td>{sus_val_str}</td>"
                         else:
                             # If susceptibility value itself is missing
                             html_content += "<td>N/A</td>"
                     else:
                         # Add placeholder if no result was found for this observable/column combo
                         html_content += "<td>N/A</td>"
                 html_content += "</tr>" # End observable row

            html_content += "</tbody></table>" # End susceptibility tabl


    # --- Plots ---
    html_content += "<h2>Plots</h2>"
    if plot_filenames:
        plot_filenames.sort()
        for plot_file in plot_filenames:
             relative_plot_path = os.path.basename(plot_file)
             plot_title = os.path.splitext(relative_plot_path)[0].replace("_", " ").replace(" vs ", " vs ").replace(" by ", " by ").title()
             html_content += f'<h3>{plot_title}</h3>\n'
             html_content += f'<img src="{relative_plot_path}" alt="Plot: {relative_plot_path}"><br>\n'
    else:
        html_content += "<p>No plots were generated or provided.</p>"


    # --- Raw Results Data (Optional JSON dump ---
    # html_content += "<h2>Raw Processed Data (JSON)</h2>"
    # try:
    #     serializable_results = []
    #     for item in results_list:
    #         if is_dataclass(item) and not isinstance(item, type):
    #             serializable_results.append(asdict(item))
    #         elif isinstance(item, dict):
    #              serializable_results.append(item)
    #     json_data = json.dumps(serializable_results, indent=4, default=str)
    #     html_content += f"<pre>{json_data}</pre>"
    # except Exception as e:
    #     html_content += f"<p>Error converting results to JSON: {e}</p>"
    html_content += """
    </body>
    </html>
    """

    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"HTML report saved to {filepath}")
    except Exception as e:
        print(f"Error writing HTML report {filepath}: {e}")


def generate_report(results_list, plot_filenames, output_dir, table_obs_report=['charge', 'charge_no_protocol', 'total_energy']):
    table_configs_report = []

    generate_html_report(
        results_list=results_list,
        plot_filenames=plot_filenames,
        output_dir=output_dir,
        report_filename="final_report.html",
        table_observables=table_obs_report,
        table_configs=table_configs_report
    )
    print(f"Generated HTML report in {output_dir}")
