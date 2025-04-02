from dataclasses import asdict
import json
import math
import os
import utils
import numpy as np
from collections import defaultdict
from typing import List, Dict, Tuple, Any
from run_result import RunResult
from Observables import ObservableFactory, TotalEnergy, Energy_N3
from conf import Conf

class Results:
    def __init__(self, run_time, output_dir):
        self.run_time = run_time
        # Directory to save results file and plots
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

        # Store raw data temporarily during the run
        self._raw_results_buffer: List[Tuple[Conf, str, str, Dict, Dict, int, str | None]] = []
        # Final processed results
        self.processed_results: List[RunResult] = []

    def add_raw_result(self, conf: Conf, obs_name: str, backend_name: str, noise_params: Dict,
                       counts: Dict, total_shots: int, job_id: str | None = None):
        """Temporarily stores raw results from a run."""
        self._raw_results_buffer.append(
            (conf, obs_name, backend_name, noise_params, counts, total_shots, job_id)
        )

    def process_results(self, observable_factory: ObservableFactory):
        """Processes raw results, calculates values, and handles derived observables."""
        print("Processing raw results...")
        self.processed_results = []
        obs_dict = observable_factory.obs_dict

        # --- Process Directly Simulated Observables ---
        for conf, obs_name, backend_name, noise_params, counts, total_shots, job_id in self._raw_results_buffer:
            observable = obs_dict.get(obs_name)
            if not observable or isinstance(observable, Energy_N3): # Skip N3 for now
                continue
            if hasattr(observable, 'is_derived_observable') and observable.is_derived_observable():
                continue

            # Calculate primary metrics
            exp_val, sem = observable.calculate_expectation_and_sem(counts, total_shots)
            susceptibility = observable.calculate_susceptibility(counts)
            correlation = Results.calculate_correlation(counts, conf.N)

            # Extract relevant conf parameters
            conf_params = {
                'h': conf.h, 'k': conf.k, 'total_shots': conf.total_shots,
                'delay_time': conf.delay_time, 'N': conf.N,
                'p_dephase': conf.p_dephase, 'theta': conf.theta, 'xor_alice_res': conf.xor_alice_res
            }

            run_result = RunResult(
                observable_name=obs_name,
                conf_params=conf_params,
                backend_name=backend_name,
                run_type='simulator' if noise_params else ('sampler'), # Determine run_type better
                noise_params=noise_params,
                counts=counts,
                total_shots=total_shots,
                job_id=job_id,
                expectation_value=exp_val,
                sem=sem,
                susceptibility=susceptibility,
                correlation=correlation,
                is_derived=False
            )
            self.processed_results.append(run_result)

        # --- Calculate Derived Observables (Example: TotalEnergy) ---
        self._calculate_derived_total_energy(observable_factory)

        # --- Calculate Final E_B for N=3 Runs ---
        self._calculate_energy_n3(observable_factory)

        # Clear buffer after processing
        self._raw_results_buffer = []
        print(f"Processing complete. {len(self.processed_results)} results generated.")

    def _calculate_derived_total_energy(self, observable_factory: ObservableFactory):
        """Calculates TotalEnergy from H1 and V results."""
        total_energy_obs = observable_factory.get_observable("total_energy")
        if not total_energy_obs or not isinstance(total_energy_obs, TotalEnergy):
            return # Skip if TotalEnergy observable isn't defined properly

        print("Calculating derived observable: total_energy")
        h1_results = [res for res in self.processed_results if res.observable_name == "h1"]
        v_results = [res for res in self.processed_results if res.observable_name == "v"]

        # Match H1 and V results based on configuration, backend, noise etc.
        grouped_results: Dict[Tuple, Dict[str, RunResult]] = {}

        for res in h1_results + v_results:
             # Create a unique key based on parameters that should match
             key = (
                 tuple(sorted(res.conf_params.items())), # Convert dict to tuple of tuples
                 res.backend_name,
                 res.run_type,
                 tuple(sorted(res.noise_params.items()))
             )
             if key not in grouped_results:
                 grouped_results[key] = {}
             if res.observable_name in total_energy_obs.get_component_names():
                  grouped_results[key][res.observable_name] = res

        # Calculate TotalEnergy for matched pairs
        new_total_energy_results = []
        for key, components in grouped_results.items():
            if "h1" in components and "v" in components:
                h1_res = components["h1"]
                v_res = components["v"]

                # Check if expectation values are valid
                if h1_res.expectation_value is None or v_res.expectation_value is None or \
                   h1_res.sem is None or v_res.sem is None:
                    print(f"Warning: Missing data for TotalEnergy calculation for key {key}. Skipping.")
                    continue

                assert h1_res.conf_params['h'] == v_res.conf_params['h'] and h1_res.conf_params['k'] == v_res.conf_params['k']
                h = h1_res.conf_params['h']
                k = v_res.conf_params['k']

                gs_energy = -(h**2 + 2*k**2)/math.sqrt(h**2 + k**2)
                # Calculate derived values
                total_exp_val = h * h1_res.expectation_value + 2 * k * v_res.expectation_value
                exp_val_diff = total_exp_val - gs_energy
                # Combine SEM: sqrt(sem1^2 + sem2^2)
                total_sem = math.sqrt(h1_res.sem**2 + v_res.sem**2)

                # Create a new RunResult for TotalEnergy
                total_energy_result = RunResult(
                    observable_name=total_energy_obs.name,
                    timestamp=max(h1_res.timestamp, v_res.timestamp), # Use latest timestamp
                    conf_params=h1_res.conf_params, # Assumes conf matches
                    backend_name=h1_res.backend_name,
                    run_type=h1_res.run_type,
                    noise_params=h1_res.noise_params,
                    counts={}, # No direct counts for derived observable
                    total_shots=h1_res.total_shots, # Or average/sum? Use one for reference.
                    job_id=f"derived_from_{h1_res.job_id or 'sim'}_{v_res.job_id or 'sim'}",
                    expectation_value=exp_val_diff,
                    sem=total_sem,
                    susceptibility=None, # Susceptibility needs dedicated calculation
                    correlation=None,
                    is_derived=True
                )
                new_total_energy_results.append(total_energy_result)
            else:
                print(f"Debug: Missing H1 or V for key {key}")

        self.processed_results.extend(new_total_energy_results)
        print(f"Added {len(new_total_energy_results)} derived TotalEnergy results.")

    def _calculate_energy_n3(self, observable_factory: ObservableFactory):
        """
        Calculates the final E_B for the N=3 QKD protocol by combining
        expectation values, potentially averaged over Alice's bases.

        ASSUMPTION: Raw results buffer contains expectation values for H_B
                    (or data to calculate them) from runs of QKD_Energy_N3 observables,
                    keyed by configuration (J, theta, xor_alice_res) and alice_basis.
                    This might require adapting how results are stored if using Estimator.
        """
        print("Calculating derived observable: qkd_energy_n3 (E_B)")
        # 1. Filter raw results for QKD_Energy_N3 runs
        qkd_raw_results = []
        # This part depends heavily on how you store Estimator results
        # Let's assume _raw_results_buffer stores tuples like:
        # (conf, obs_name, backend_name, noise_params, expectation_value_H_B, sem_H_B, total_shots, job_id)
        # OR if using sampler: (conf, obs_name, ..., counts, ...) and calculate <H_B> here.

        # Simplified structure: Group results needed for final E_B calculation
        # Key: (conf_tuple, xor_alice_res)
        # Value: {'X': RunResult_for_AliceX, 'Y': RunResult_for_AliceY}
        grouped_for_eb = defaultdict(dict)

        # --- This loop needs actual implementation based on stored results format ---
        # Example assuming buffer stores RunResult-like objects with expectation values
        processed_qkd_results_temp = [] # Store intermediate processed N3 runs
        for raw_data_tuple in self._raw_results_buffer:
             # Adapt this unpacking based on actual buffer contents
             conf, obs_name, backend, noise, counts, shots, job_id = raw_data_tuple
             observable = observable_factory.get_observable(obs_name)

             if not isinstance(observable, Energy_N3):
                 continue

             # --- Calculate <H_B> from counts if using Sampler ---
             # If using Estimator, expectation value might be directly available
             # Example with counts: Need to measure terms like X1X2, Z2
             # This requires running specific measurement circuits AND THEN combining.
             # Let's assume for now <H_B> is directly available in raw_data_tuple or calculated easily
             # Placeholder: Use expectation_value field if it stores <H_B>
             exp_val_h_b = raw_data_tuple[4] # Hypothetical index for <H_B>
             sem_h_b = raw_data_tuple[5]      # Hypothetical index for SEM(<H_B>)

             conf_params_dict = conf.__dict__ # Or specific relevant params
             run_result = RunResult( # Create a temporary result for this specific run
                  observable_name=obs_name,
                  conf_params=conf_params_dict,
                  backend_name=backend,
                  run_type='estimator' if exp_val_h_b is not None else 'sampler', # Example logic
                  noise_params=noise,
                  counts=counts, # Store counts if available
                  total_shots=shots,
                  job_id=job_id,
                  expectation_value=exp_val_h_b, # Store <H_B> here
                  sem=sem_h_b,
                  # susceptibility=None, correlation=None, # Not directly relevant for E_B
                  is_derived=False # This specific run isn't derived, the final E_B will be
             )
             processed_qkd_results_temp.append(run_result)
        # --- End of hypothetical processing loop ---


        # 2. Group the processed intermediate results
        for res in processed_qkd_results_temp:
             conf_tuple = tuple(sorted(res.conf_params.items())) # Unique key for config
             xor_res = res.conf_params.get('xor_alice_res', 0)
             group_key = (conf_tuple, xor_res, res.backend_name, res.run_type, tuple(sorted(res.noise_params.items())))

             obs_name = res.observable_name
             if "alice_x" in obs_name:
                 grouped_for_eb[group_key]['X'] = res
             elif "alice_y" in obs_name:
                 grouped_for_eb[group_key]['Y'] = res

        # 3. Calculate final E_B for each group where both X and Y results exist
        new_eb_results = []
        for key, results_dict in grouped_for_eb.items():
             if 'X' in results_dict and 'Y' in results_dict:
                 res_x = results_dict['X']
                 res_y = results_dict['Y']

                 # Ensure required values exist
                 if res_x.expectation_value is None or res_y.expectation_value is None or \
                    res_x.sem is None or res_y.sem is None:
                      print(f"Warning: Missing <H_B> data for E_B calculation for key {key}. Skipping.")
                      continue

                 # Average expectation values over Alice's bases
                 avg_exp_val_h_b = 0.5 * (res_x.expectation_value + res_y.expectation_value)
                 # Combine SEMs (assuming independence of X/Y runs): sqrt( (0.5*semX)^2 + (0.5*semY)^2 )
                 avg_sem_h_b = 0.5 * np.sqrt(res_x.sem**2 + res_y.sem**2)

                 # Retrieve E_B_gs (pre-calculated in QKD_Energy_N3)
                 # Need the observable instance to get it - assumes factory holds the relevant one
                 # This might require getting the observable based on conf (J value)
                 j_val = res_x.conf_params.get('k', None) # Get J from the results config
                 e_b_gs = 0.0
                 temp_conf_for_j = Conf() # Create dummy conf
                 temp_conf_for_j.J = j_val
                 temp_conf_for_j.N = 3
                 # Need to handle potential error if observable not found or J is None
                 try:
                      # Get *either* X or Y observable instance, E_B_gs should be the same
                      qkd_obs_instance = observable_factory.get_observable(f"qkd_energy_n3_alice_x")
                      if qkd_obs_instance and hasattr(qkd_obs_instance, 'k') and qkd_obs_instance.k == j_val:
                          e_b_gs = qkd_obs_instance.E_B_gs
                      else: # Try to reconstruct if factory doesn't hold right J value
                          dummy_obs = Energy_N3(temp_conf_for_j, 'X')
                          e_b_gs = dummy_obs.E_B_gs
                 except Exception as e:
                      print(f"Could not retrieve E_B_gs for J={j_val}: {e}")


                 # Calculate final E_B
                 final_eb_value = avg_exp_val_h_b - e_b_gs
                 final_eb_sem = avg_sem_h_b # SEM of E_B_gs is assumed 0 if calculated analytically

                 # Create the final RunResult for E_B
                 conf_tuple, xor_res, backend_name, run_type, noise_tuple = key
                 conf_params = dict(conf_tuple) # Convert back to dict

                 eb_result = RunResult(
                      observable_name=f"E_B_n3_xor{xor_res}", # Name for the derived value
                      timestamp=max(res_x.timestamp, res_y.timestamp),
                      conf_params=conf_params,
                      backend_name=backend_name,
                      run_type=run_type,
                      noise_params=dict(noise_tuple),
                      counts={}, # No direct counts
                      total_shots=res_x.total_shots, # Reference shots from one run
                      job_id=f"derived_eb_{res_x.job_id}_{res_y.job_id}",
                      expectation_value=final_eb_value,
                      sem=final_eb_sem,
                      susceptibility=None, correlation=None,
                      is_derived=True # Mark as derived
                 )
                 new_eb_results.append(eb_result)
             else:
                 print(f"Debug: Missing Alice X or Y basis result for key {key}")

        self.processed_results.extend(new_eb_results)
        print(f"Added {len(new_eb_results)} derived QKD E_B (N=3) results.")


    def save_results(self, filename="processed_results.json"):
        """Saves the processed results list to a JSON file."""
        filepath = os.path.join(self.output_dir, filename)
        try:
            # Convert list of dataclasses to list of dicts for JSON serialization
            results_dict_list = [asdict(res) for res in self.processed_results]
            with open(filepath, 'w') as f:
                json.dump(results_dict_list, f, indent=4, default=str) # Use default=str for non-serializable types like datetime
            print(f"Processed results saved to {filepath}")
        except Exception as e:
            print(f"Error saving results to {filepath}: {e}")

    def load_results(self, filename="processed_results.json"):
        """Loads processed results from a JSON file."""
        filepath = os.path.join(self.output_dir, filename)
        try:
            with open(filepath, 'r') as f:
                results_dict_list = json.load(f)
            # Convert list of dicts back to list of RunResult objects
            # This might require handling datetime parsing etc.
            self.processed_results = [RunResult(**data) for data in results_dict_list]
            print(f"Processed results loaded from {filepath}")
        except FileNotFoundError:
            print(f"Results file not found: {filepath}")
            self.processed_results = []
        except Exception as e:
            print(f"Error loading results from {filepath}: {e}")
            self.processed_results = []

    @staticmethod
    def calculate_correlation(counts: dict, num_qubits: int):
        if not counts: return 0.0

        total_counts = sum(counts.values())
        if total_counts == 0: return 0.0

        correlation = 0.0
        expected_len = num_qubits # Expected bitstring length

        for bitstring, count in counts.items():
            # Ensure bitstring has correct length
            if len(bitstring) != expected_len:
                print(f"Warning: Skipping bitstring '{bitstring}' in correlation calc due to unexpected length.")
                continue

            # Map '0' -> +1, '1' -> -1 for Z measurement eigenvalue
            try:
                # Use indices based on 'b1b0' format
                outcome_q0 = 1.0 if bitstring[utils.get_counts_bob_qubit_idx(num_qubits)] == '0' else -1.0 # Bob's value
                outcome_q1 = 1.0 if bitstring[utils.get_counts_alice_qubit_idx(num_qubits)] == '0' else -1.0 # Alice's value
                correlation += outcome_q1 * outcome_q0 * count
            except IndexError:
                print(f"Warning: Skipping bitstring '{bitstring}' in correlation calc due to index error.")

        return correlation / total_counts if total_counts > 0 else 0.0
