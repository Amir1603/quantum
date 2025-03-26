from dataclasses import asdict
import json
import math
import os
from typing import List, Dict, Tuple, Any
from run_result import RunResult
from Observables import ObservableFactory, TotalEnergy
from conf import Conf
from constants import *


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
            if not observable:
                print(f"Warning: Observable '{obs_name}' not found in factory. Skipping.")
                continue
            if hasattr(observable, 'is_derived_observable') and observable.is_derived_observable():
                continue

            # Calculate primary metrics
            exp_val, sem = observable.calculate_expectation_and_sem(counts, total_shots)
            susceptibility = observable.calculate_susceptibility(counts)
            correlation = Results.calculate_correlation(counts, conf.n_qubits)

            # Extract relevant conf parameters
            conf_params = {
                'h': conf.h, 'k': conf.k, 'total_shots': conf.total_shots,
                'delay_time': conf.delay_time, 'n_qubits': conf.n_qubits,
                'p_dephase': conf.p_dephase
            }

            run_result = RunResult(
                observable_name=obs_name,
                conf_params=conf_params,
                backend_name=backend_name,
                run_type='simulator' if noise_params else ('sampler' or 'estimator'), # Determine run_type better
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

                # Calculate derived values
                total_exp_val = h1_res.expectation_value + v_res.expectation_value
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
                    expectation_value=total_exp_val,
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
        """
        Calculates the Z0Z1 correlation. Assumes bitstring format 'b1b0'.
        Adjust ALICE_QUBIT_IDX and BOB_QUBIT_IDX if format is different.
        """
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
                outcome_q0 = 1.0 if bitstring[BOB_QUBIT_IDX] == '0' else -1.0 # Bob's value
                outcome_q1 = 1.0 if bitstring[ALICE_QUBIT_IDX] == '0' else -1.0 # Alice's value
                correlation += outcome_q1 * outcome_q0 * count
            except IndexError:
                print(f"Warning: Skipping bitstring '{bitstring}' in correlation calc due to index error.")

        return correlation / total_counts if total_counts > 0 else 0.0
