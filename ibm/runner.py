from conf import Conf
from Observables import Observable
from qiskit_aer import Aer, AerSimulator
from qiskit_aer.noise import NoiseModel, phase_damping_error
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
from results import Results
import plotting
import utils


class Runner():
    def __init__(self, observables: list[Observable]):
        self.noise_model = None
        self.observables = observables
        self.service = QiskitRuntimeService()

    def __choose_backend(self, backend_name, conf: Conf):
        if self.noise_model or (not conf.run_sampler):
            return AerSimulator(noise_model=self.noise_model)
        elif backend_name:
            return self.service.backend(backend_name)
        else:
            return self.service.least_busy(operational=True, simulator=False)

    def _create_noise_model(self, p_dephase):
        if not p_dephase or p_dephase == 0:
            self.noise_model = None
            return
        # Create dephasing error
        dephase_error = phase_damping_error(p_dephase)
        noise_model = NoiseModel()
        # Apply error more selectively if possible based on gate times and delay
        noise_model.add_all_qubit_quantum_error(dephase_error, ['delay', 'id', 'measure', 'rz', 'sx', 'x']) # Example gates (Add 'cx'??)
        self.noise_model = noise_model

    def init_run_level(self, conf: Conf, backend_name: str | None = None):
         """ Initialize backend and noise for a specific configuration (h, k, delay etc.) """
         self.backend = self.__choose_backend(backend_name, conf)
         self._create_noise_model(conf.p_dephase) # Create noise model based on conf

         print(f"\n--- Initialized Run Level ---")
         print(f"  Conf: h={conf.h}, k={conf.k}, shots={conf.total_shots}, p_dephase={conf.p_dephase}, delay={conf.delay_time}")
         print(f"  Backend: {self.backend.name}")
         print(f"  Noise Model Active: {self.noise_model is not None}")

         # Note: SamplerV2 might handle noise models differently or require AerProvider
         use_primitives = conf.run_sampler
         self.sampler = SamplerV2(mode=self.backend) if use_primitives else None
         # Keep AerSimulator separate for explicit simulator runs
         self.simulator = AerSimulator(noise_model=self.noise_model)

    def _qet_circuit(self, obs: Observable, conf: Conf):
        num_qubits = conf.N
        qubit_indices = list(range(num_qubits))

        # --- Determine required classical bits ---
        if conf.N == 3:
            # CONSISTENTLY use 3 classical bits for all N=3 simulation runs
            # (Alice, Bob Z2, Intermediate Z1) even if not all are measured by the specific observable
            num_clbits = 3
            print(f"  N=3 run: Using {num_clbits} classical bits.")
        elif conf.N == 2:
            # Logic for N=2 runs (e.g., 2 classical bits)
            num_clbits = 2 # Adjust if needed for specific N=2 observables
            print(f"  N=2 run: Using {num_clbits} classical bits.")
        else:
            raise NotImplementedError(f"Unsupported N={conf.N} in _qet_circuit")

        # Define classical register indices based on utils (Alice=c0, BobZ2=c1, IntermedZ1=c2)
        alice_creg = utils.get_counts_alice_creg_idx(num_qubits)
        bob_z2_creg = utils.get_counts_bob_creg_idx(num_qubits)
        intermed_z1_creg = utils.get_counts_intermediate_creg_idx(num_qubits) # Expect 2 (or None if N!=3)

        qc = QuantumCircuit(num_qubits, num_clbits) # Use determined num_clbits
        qc.name = f'{obs.name}_qc'

        # Prepare the ground state
        obs.apply_ground_state(qc, list(range(num_qubits)))

        alice_creg_idx = utils.get_alice_qubit_idx(num_qubits)
        bob_creg_idx = utils.get_bob_qubit_idx(num_qubits)

        obs.apply_alice_measurement(qc, utils.get_alice_qubit_idx(num_qubits), alice_creg_idx)

        # Idle Bob’s qubit
        if conf.delay_time and conf.delay_time > 0:
             # Ensure delay_time is in appropriate units (dt, sec). Assume dt for Aer.
             qc.delay(conf.delay_time, utils.get_bob_qubit_idx(num_qubits), unit='dt')

        # Bob's conditional operation
        # Pass the classical register/bit index Alice measured into
        obs.apply_bob_operation(qc, utils.get_bob_qubit_idx(num_qubits), alice_creg_idx, conf.xor_alice_res)

        # Bob's measurement basis
        bob_meas_basis = obs.get_bob_measurement_basis()
        if conf.N == 3:
            intermed_q_idx = 1
            bob_q_idx = utils.get_bob_qubit_idx(num_qubits) # Should be 2
            if bob_meas_basis == "X1X2":
                print(f"  Adding measurements for X1X2 (H on q1, q2; Measure q1->c{intermed_z1_creg}, q2->c{bob_z2_creg})")
                qc.h(intermed_q_idx)
                qc.h(bob_q_idx)
                # Ensure using the correct classical bit objects/indices
                qc.measure(intermed_q_idx, qc.clbits[intermed_z1_creg])
                qc.measure(bob_q_idx, qc.clbits[bob_z2_creg])
            elif bob_meas_basis == "Z2":
                print(f"  Adding measurement for Z2 (Measure q2->c{bob_z2_creg})")
                # Measure Bob into the correct classical bit
                qc.measure(bob_q_idx, qc.clbits[bob_z2_creg])
                # Note: clbit[intermed_z1_creg] (index 2) remains unused for this specific circuit run
            # else: handle other N=3 cases?
        elif conf.N == 2:
            if bob_meas_basis == "X":
                qc.h(utils.get_bob_qubit_idx(num_qubits))
            elif bob_meas_basis == "Y":
                qc.sdg(utils.get_bob_qubit_idx(num_qubits)) # Apply S dagger
                qc.h(utils.get_bob_qubit_idx(num_qubits))

            qc.measure(utils.get_bob_qubit_idx(num_qubits), bob_creg_idx)

        return qc

    def _run_sim(self, qc, total_shots):
        # Use the Qiskit simulator
        try:
            qc_compiled = transpile(qc, self.simulator)
            job_sim = self.simulator.run(qc_compiled, shots=total_shots)
            result_sim = job_sim.result()
            counts_sim = result_sim.get_counts(qc_compiled)

            formatted_counts = {bitstr.replace(' ', ''): count for bitstr, count in counts_sim.items()}
            return formatted_counts, job_sim.job_id()
        except Exception as e:
            print(f"Error running simulation for {qc.name}: {e}")
            return {}, None


    def _run_sampler(self, qc, total_shots):
        if not self.sampler:
             print("Sampler not initialized.")
             return {}, None
        try:
             qc_transpiled = transpile(qc, self.backend)
             job = self.sampler.run([qc_transpiled], shots=total_shots)
             result = job.result()
             # SamplerV2 returns data slightly differently
             pub_result = result[0]
             # Get counts, format bitstrings (often hex in V2)
             raw_counts = pub_result.data.meas.get_counts()

             num_bits = qc.num_clbits
             binary_counts = {}
             for hex_key, count in raw_counts.items():
                 binary_key = format(int(hex_key, 16), f'0{num_bits}b')
                 binary_counts[binary_key] = count

             # No direct density matrix from SamplerV2
             return binary_counts, job.job_id()
        except Exception as e:
            print(f"Error running sampler for {qc.name}: {e}")
            return {}, None

    def execute_observable(self, obs: Observable, conf: Conf, results: Results):
        """Executes simulation/run for a single observable and adds raw result."""

        print(f"  Executing: {obs.name}")
        qc = self._qet_circuit(obs, conf)
        plotting.draw_circuit(qc, results.output_dir, conf)

        counts = {}
        job_id = None
        backend_name_used = self.backend.name
        noise_params_used = {'p_dephase': conf.p_dephase} if conf.p_dephase else {}
        run_type = 'unknown'


        if conf.run_simulator:
            run_type = 'simulator'
            counts, job_id = self._run_sim(qc, conf.total_shots)
            # Add raw results immediately
            if counts:
                 results.add_raw_result(conf, obs, backend_name_used, noise_params_used, counts, conf.total_shots, job_id)

        if conf.run_sampler:
            run_type = 'sampler'
            # Ensure backend is suitable for Sampler (not AerSimulator unless provider setup allows)
            if isinstance(self.backend, AerSimulator):
                 print(f"Warning: Skipping Sampler run for {obs.name} on AerSimulator. Use a real backend or configure AerProvider.")
            else:
                 counts_hw, job_id_hw = self._run_sampler(qc, conf.total_shots)
                 if counts_hw:
                     # Use actual backend name and no explicit noise params dict if using backend noise implicitly
                     results.add_raw_result(conf, obs, self.backend.name, {}, counts_hw, conf.total_shots, job_id_hw)

        if not conf.run_simulator and not conf.run_sampler:
             print(f"  Skipping execution for {obs.name} as no run type is enabled.")
