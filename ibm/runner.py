from conf import Conf
from Observables import Observable
from qiskit_aer import Aer, AerSimulator
from qiskit_aer.noise import NoiseModel, phase_damping_error
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2, EstimatorV2
from results import Results
from constants import *
import plotting


class Runner():
    def __init__(self, observables: list[Observable]):
        self.noise_model = None
        self.observables = observables
        self.service = QiskitRuntimeService()

    def __choose_backend(self, backend_name, conf: Conf):
        if self.noise_model or (not conf.run_sampler and not conf.run_estimator):
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

         # Initialize sampler/estimator if needed (based on conf, not noise model directly)
         # Note: SamplerV2/EstimatorV2 might handle noise models differently or require AerProvider
         use_primitives = conf.run_sampler or conf.run_estimator
         self.estimator = EstimatorV2(mode=self.backend) if use_primitives else None
         self.sampler = SamplerV2(mode=self.backend) if use_primitives else None
         # Keep AerSimulator separate for explicit simulator runs
         self.simulator = AerSimulator(noise_model=self.noise_model)

    def _qet_circuit(self, obs: Observable, conf: Conf):
        # ... circuit construction logic using obs and conf ...
        # Ensure num_qubits comes from conf or is fixed
        num_qubits = conf.n_qubits
        qc = QuantumCircuit(num_qubits, num_qubits)
        qc.name = f'{obs.name}_qc'

        # Prepare the ground state
        obs.apply_ground_state(qc, list(range(num_qubits)))

        alice_creg_idx = ALICE_QUBIT_IDX
        bob_creg_idx = BOB_QUBIT_IDX

        obs.apply_alice_measurement(qc, ALICE_QUBIT_IDX, alice_creg_idx)

        # Idle Bob’s qubit
        if conf.delay_time and conf.delay_time > 0:
             # Ensure delay_time is in appropriate units (dt, sec). Assume dt for Aer.
             qc.delay(conf.delay_time, BOB_QUBIT_IDX, unit='dt')

        # Bob's conditional operation
        # Pass the classical register/bit index Alice measured into
        obs.apply_bob_operation(qc, BOB_QUBIT_IDX, alice_creg_idx)

        # Bob's measurement basis
        bob_basis = obs.get_bob_measurement_basis()
        if bob_basis == "X":
            qc.h(BOB_QUBIT_IDX)
        elif bob_basis == "Y":
             qc.sdg(BOB_QUBIT_IDX) # Apply S dagger
             qc.h(BOB_QUBIT_IDX)

        qc.measure(BOB_QUBIT_IDX, bob_creg_idx)

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
        plotting.draw_circuit(qc, results.output_dir)

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
                 results.add_raw_result(conf, obs.name, backend_name_used, noise_params_used, counts, conf.total_shots, job_id)

        if conf.run_sampler:
            run_type = 'sampler'
            # Ensure backend is suitable for Sampler (not AerSimulator unless provider setup allows)
            if isinstance(self.backend, AerSimulator):
                 print(f"Warning: Skipping Sampler run for {obs.name} on AerSimulator. Use a real backend or configure AerProvider.")
            else:
                 counts_hw, job_id_hw = self._run_sampler(qc, conf.total_shots)
                 if counts_hw:
                     # Use actual backend name and no explicit noise params dict if using backend noise implicitly
                     results.add_raw_result(conf, obs.name, self.backend.name, {}, counts_hw, conf.total_shots, job_id_hw)

        if not conf.run_simulator and not conf.run_sampler:
             print(f"  Skipping execution for {obs.name} as no run type is enabled.")
