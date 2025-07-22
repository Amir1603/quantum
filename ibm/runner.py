from conf import QuantumSimConf
from Observables import Observable
from qiskit_aer import Aer, AerSimulator
import qiskit_aer.noise as noise
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
from results import Results
import plotting
import utils


class Runner():
    def __init__(self, observables: list[Observable], service: QiskitRuntimeService = None):
        self.noise_model = None
        self.observables = observables
        self.service = service

    def __choose_backend(self, backend_name, conf: QuantumSimConf):
        if self.noise_model or (not conf.run_sampler):
            return AerSimulator(method="density_matrix", noise_model=self.noise_model)
        elif backend_name:
            return self.service.backend(backend_name)
        else:
            return self.service.least_busy(operational=True, simulator=False)

    def _create_noise_model(self, conf: QuantumSimConf):
        p_dephase = conf.p_dephase

        noise_model = noise.NoiseModel()

        # Create dephasing error
        if p_dephase and p_dephase != 0:
            dephase_error = noise.phase_damping_error(p_dephase)
            # Apply error more selectively if possible based on gate times and delay
            noise_model.add_all_qubit_quantum_error(dephase_error, ['delay', 'id', 'measure', 'h', 'ry', 'sdg', 'rx'])

        self.noise_model = noise_model

    def init_run_level(self, conf: QuantumSimConf, backend_name: str | None = None):
         """ Initialize backend and noise for a specific configuration (h, J, delay etc.) """
         self.backend = self.__choose_backend(backend_name, conf)
         self._create_noise_model(conf)

         print(f"\n--- Initialized Run Level ---")
         print(f"  Conf: h={conf.h}, J={conf.J}, shots={conf.total_shots}, p_dephase={conf.p_dephase}, delay={conf.delay_time}")

         # Note: SamplerV2 might handle noise models differently or require AerProvider
         use_primitives = conf.run_sampler
         self.sampler = SamplerV2(mode=self.backend) if use_primitives else None
         # Keep AerSimulator separate for explicit simulator runs
         self.simulator = AerSimulator(noise_model=self.noise_model)

    def _apply_measurements(self, obs: Observable, qc: QuantumCircuit, N: int):
        bob_idx = utils.get_bob_idx(N)
        bob_meas_basis = obs.get_bob_measurement_basis()

        alice_idx = utils.get_alice_idx(N)
        bob_neighbor_idx = utils.get_bob_neighbor_idx(N)

        utils.apply_basis(qc, bob_meas_basis, bob_idx)

        qc.measure(bob_idx, bob_idx)

        # Act on Bob's neighbor only if N is big enough such that it is different from Alice's qubit
        if alice_idx != bob_neighbor_idx:
            utils.apply_basis(qc, bob_meas_basis, bob_neighbor_idx)
            qc.measure(bob_neighbor_idx, bob_neighbor_idx)

    def _qet_circuit(self, obs: Observable, conf: QuantumSimConf, is_simulator: bool):
        num_qubits = conf.N+1

        # Consistently use N classical bits for arbitrary N simulation runs
        # even if not all are measured by the specific observable
        num_clbits = conf.N+1

        qc = QuantumCircuit(num_qubits, num_clbits)
        qc.name = f'{obs.name}_qc'

        # Prepare the ground state
        obs.apply_ground_state(qc, use_density_matrix=is_simulator)

        obs.apply_alice_measurement(qc)

        # Idle Bob’s qubit
        if conf.delay_time and conf.delay_time > 0:
            # Ensure delay_time is in appropriate units (dt, sec). Assume dt for Aer.
            bob_idx = utils.get_bob_idx(conf.N)
            qc.delay(conf.delay_time, bob_idx, unit='dt')

        # Bob's conditional operation
        # Pass the classical register/bit index Alice measured into
        obs.apply_bob_operation(qc, conf.xor_alice_res)

        self._apply_measurements(obs, qc, conf.N)

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
             raw_counts = pub_result.data.c.array

             num_bits = qc.num_clbits
             binary_counts = {}
             for res in raw_counts:
                 res = res[0]
                 binary_key = format(res, f'0{num_bits}b')

                 if binary_key not in binary_counts:
                    binary_counts[binary_key] = 0

                 binary_counts[binary_key] = binary_counts[binary_key] + 1

             # No direct density matrix from SamplerV2
             return binary_counts, job.job_id()
        except Exception as e:
            print(f"Error running sampler for {qc.name}: {e}")
            return {}, None

    def execute_observable(self, obs: Observable, conf: QuantumSimConf, results: Results):
        """Executes simulation/run for a single observable and adds raw result."""

        print(f"  Executing: {obs.name}")
        counts = {}
        job_id = None
        backend_name_used = self.backend.name
        noise_params_used = {'p_dephase': conf.p_dephase} if conf.p_dephase else {}

        if conf.run_simulator:
            qc = self._qet_circuit(obs, conf, is_simulator=True)
            plotting.draw_circuit(qc, results.output_dir, conf)

            counts, job_id = self._run_sim(qc, conf.total_shots)
            # Add raw results immediately
            if counts:
                 results.add_raw_result(conf, obs, backend_name_used, noise_params_used, counts, conf.total_shots, job_id)

        if conf.run_sampler:
            qc = self._qet_circuit(obs, conf, is_simulator=False)
            plotting.draw_circuit(qc, results.output_dir, conf)

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
