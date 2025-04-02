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
            if not observable:
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
                'p_dephase': conf.p_dephase, 'theta': conf.theta,
                'xor_alice_res': conf.xor_alice_res,
                'alice_basis': getattr(observable, 'alice_basis', None)
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

        # --- Calculate Derived Observables ---
        self._calculate_all_derived_observables(observable_factory, self.processed_results)

        # Clear buffer after processing
        self._raw_results_buffer = []
        print(f"Processing complete. {len(self.processed_results)} results generated.")

    def _calculate_all_derived_observables(self, observable_factory: ObservableFactory, current_results: list):
        """
        Iterates through all known derived observables and calculates their values.
        """
        print("Calculating derived observables...")
        newly_derived_results = []

        # Group results by configuration to make lookups easier
        # Key: tuple(sorted(conf_params.items())) + backend + run_type + tuple(sorted(noise.items()))
        grouped_results: Dict[Tuple, Dict[str, RunResult]] = defaultdict(dict)
        for res in current_results:
             key = (
                  tuple(sorted(res.conf_params.items())),
                  res.backend_name,
                  res.run_type,
                  tuple(sorted(res.noise_params.items()))
             )
             grouped_results[key][res.observable_name] = res

        # Iterate through all observables in the factory, find derived ones
        for obs_name, observable in observable_factory.obs_dict.items():
            if not hasattr(observable, 'is_derived_observable') or not observable.is_derived_observable():
                continue

            print(f"  Attempting to calculate derived: {obs_name}")
            # Iterate through configurations where components might exist
            for key, component_dict in grouped_results.items():
                 conf_params_tuple, backend_name, run_type, noise_params_tuple = key
                 conf_params = dict(conf_params_tuple)

                 # Check if this derived observable applies to this N value
                 if conf_params.get('N') != observable.N:
                      continue

                 # --- Get components needed by this derived observable ---
                 required_components = observable.get_component_names()
                 available_components = {name: component_dict.get(name) for name in required_components}

                 # Check if all components are available for this config
                 if all(comp is not None for comp in available_components.values()):
                      # Calculate the derived value using the observable's method
                      if hasattr(observable, 'calculate_derived_value_and_sem'):
                           derived_value, derived_sem = observable.calculate_derived_value_and_sem(available_components)

                           if derived_value is not None and derived_sem is not None:
                               # Create RunResult for the derived observable
                               # Use data from one of the components for common fields
                                ref_res = next(iter(available_components.values()))
                                derived_run_result = RunResult(
                                     observable_name=obs_name,
                                     timestamp=ref_res.timestamp, # Or max timestamp
                                     conf_params=conf_params,
                                     backend_name=backend_name,
                                     run_type=run_type,
                                     noise_params=dict(noise_params_tuple),
                                     counts={}, # No direct counts
                                     total_shots=ref_res.total_shots,
                                     job_id=f"derived_{obs_name}", # Simple derived ID
                                     expectation_value=derived_value,
                                     sem=derived_sem,
                                     is_derived=True
                                )
                                newly_derived_results.append(derived_run_result)
                      else:
                           print(f"Warning: Derived observable {obs_name} missing calculation method.")
                 # else: (Optional print) Components missing for this config


        # Add all newly calculated derived results to the main list
        self.processed_results.extend(newly_derived_results)
        print(f"Added {len(newly_derived_results)} derived results.")

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
