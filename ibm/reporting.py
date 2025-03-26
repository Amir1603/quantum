import os


def generate_html_report(results_list, plot_filenames, output_dir, report_filename="report.html"):
    """Generates a basic HTML report summarizing results and embedding plots."""

    filepath = os.path.join(output_dir, report_filename)

    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Quantum Simulation Report</title>
        <style>
            body { font-family: sans-serif; margin: 20px; }
            h1, h2 { color: #333; }
            img { max-width: 800px; height: auto; border: 1px solid #ddd; margin-bottom: 20px; }
            table { border-collapse: collapse; margin-bottom: 20px; }
            th, td { border: 1px solid #ccc; padding: 8px; text-align: left; }
            th { background-color: #f2f2f2; }
            pre { background-color: #f8f8f8; border: 1px solid #ddd; padding: 10px; white-space: pre-wrap; word-wrap: break-word; }
        </style>
    </head>
    <body>
        <h1>Quantum Simulation Report</h1>
    """

    # --- Summary Table (Optional) ---
    # Could create a pandas DataFrame and convert to HTML table
    # For simplicity, just list some basic info
    html_content += "<h2>Summary</h2>"
    html_content += f"<p>Total results processed: {len(results_list)}</p>"
    # Add more summary info if desired (unique confs, backends etc.)

    # --- Plots ---
    html_content += "<h2>Plots</h2>"
    if plot_filenames:
        for plot_file in plot_filenames:
             # Use relative path for embedding in HTML if plots are in the same dir
             relative_plot_path = os.path.basename(plot_file)
             html_content += f'<h3>{os.path.splitext(relative_plot_path)[0].replace("_", " ").title()}</h3>\n'
             html_content += f'<img src="{relative_plot_path}" alt="Plot: {relative_plot_path}"><br>\n'
    else:
        html_content += "<p>No plots were generated or provided.</p>"


    # --- Raw Results Data (Optional JSON dump) ---
    # html_content += "<h2>Raw Processed Data (JSON)</h2>"
    # try:
    #     from dataclasses import asdict
    #     results_dict_list = [asdict(res) for res in results_list]
    #     json_data = json.dumps(results_dict_list, indent=4, default=str)
    #     html_content += f"<pre>{json_data}</pre>"
    # except Exception as e:
    #     html_content += f"<p>Error converting results to JSON: {e}</p>"


    html_content += """
    </body>
    </html>
    """

    try:
        with open(filepath, 'w') as f:
            f.write(html_content)
        print(f"HTML report saved to {filepath}")
    except Exception as e:
        print(f"Error writing HTML report {filepath}: {e}")
