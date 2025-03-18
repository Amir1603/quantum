from analysis import Analyzer
from conf import Conf
from observable import Observable
from qiskit_aer import Aer, AerSimulator
from qiskit_aer.noise import NoiseModel, phase_damping_error
from qiskit import QuantumCircuit, transpile
from qiskit.circuit import ClassicalRegister, Delay
from qiskit.quantum_info import SparsePauliOp, DensityMatrix
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2, EstimatorV2
import numpy as np
from results import Results


class Runner():

    def __init__(self, conf: Conf, observables: list[Observable]):
        self.conf = conf
        self.noise_model = None

        self.observables = observables

        self.analyzer = None
        self.service = QiskitRuntimeService()

        Analyzer.save_conf(conf)


    def __choose_backend(self, backend_name):
        if self.noise_model or (not self.conf.run_sampler and not self.conf.run_estimator):
            return AerSimulator(noise_model=self.noise_model)
        elif backend_name:
            return self.service.backend(backend_name)
        else:
            return self.service.least_busy(operational=True, simulator=False)


    def init_run(self, p_dephase, backend_name):
        self.p_dephase = p_dephase

        if p_dephase:
            self._create_noise_model()

        self.backend = self.__choose_backend(backend_name)
        self.analyzer = Analyzer(self.conf.h, self.conf.k, self.p_dephase, self.conf.delay_time, self.backend.name)

        self.estimator = None if self.noise_model else EstimatorV2(mode=self.backend)
        self.sampler = None if self.noise_model else SamplerV2(mode=self.backend)
        self.simulator = AerSimulator(noise_model=self.noise_model)


    def finalize_run(self):
        self.analyzer.generate_html_report()


    def wrap():
        Analyzer.dump_confs()


    def _qet_circuit(self, obs: Observable, num_qubits):
        """
        Constructs the quantum circuit for the QET experiment.

        Args:
        obs: The observable to measure and create the circuit for.
        num_qubits: The number of qubits for the circuit.

        Returns:
        qc: The constructed QuantumCircuit object.
        qc_transpiled: The transpiled quantum circuit object.
        """
        qc = QuantumCircuit(2, 2)
        qc.name = f'{obs.name}_qc'

        # Prepare the ground state
        theta = -np.arccos(
            (1 / np.sqrt(2)) * np.sqrt(1 - self.conf.h / np.sqrt(self.conf.h**2 + self.conf.k**2))
        )
        qc.ry(2 * theta, 0)
        qc.cx(0, 1)

        qc.h(0)
        
        # Alice's measurement
        qc.measure(0, 0)  # Measure qubit 0 into classical bit 0

        # Idle Bob’s qubit before he acts
        if self.conf.delay_time > 0:
            delay = Delay(self.conf.delay_time)
            qc.append(delay, [1])

        # Bob's conditional operation
        phi = np.arcsin(
            (self.conf.h * self.conf.k) / np.sqrt((self.conf.h**2 + 2 * self.conf.k**2)**2 + self.conf.h**2 * self.conf.k**2)
        ) / 2

        # Bob's conditional operation
        qc.ry(2 * phi, 1).c_if(0, 0)  # Apply U(+1) if classical bit 0 is 0
        qc.ry(-2 * phi, 1).c_if(0, 1)  # Apply U(-1) if classical bit 0 is 1

        obs.apply_gate_on_qc(qc)

        qc.measure(1, 1)  # Measure qubit 1 into classical bit 1

        cr = ClassicalRegister(num_qubits, obs.name)
        qc.add_register(cr)  # Add the ClassicalRegister
        qc_transpiled = transpile(qc, self.backend)

        if self.conf.draw_circuit:
            self.analyzer.draw_circuit(qc)

        return qc, qc_transpiled


    def _create_noise_model(self):
        # Create dephasing error
        dephase_error = phase_damping_error(self.p_dephase)

        # Build the noise model
        noise_model = NoiseModel()
        noise_model.add_all_qubit_quantum_error(dephase_error, ['id', 'measure', 'rz', 'sx'])  # Affect idling and measurement steps

        self.noise_model = noise_model


    def _prep_error_mitigation(self):
        # estimator.options.default_shots = total_shots
        # estimator.options.twirling.enable_gates = True
        # estimator.options.twirling.num_randomizations = 64
        # estimator.options.twirling.shots_per_randomization = 100

        # estimator.options.dynamical_decoupling.enable = True
        # estimator.options.dynamical_decoupling.sequence_type = "XpXm"

        self.estimator.options.resilience.measure_mitigation = True
        self.estimator.options.resilience.measure_noise_learning.num_randomizations = 64
        self.estimator.options.resilience.measure_noise_learning.shots_per_randomization = 100

        # estimator.options.resilience.zne_mitigation = True
        # estimator.options.resilience.zne.noise_factors = (1, 3, 5)
        # estimator.options.resilience.zne.extrapolator = "exponential"

        self.estimator.options.resilience.zne_mitigation = True
        self.estimator.options.resilience.zne.amplifier = "pea"

        # estimator.options.resilience.pec_mitigation = True
        # estimator.options.resilience.pec.max_overhead = 100


    def _run_sim(self, qc, name):
        # Use the Qiskit simulator
        qc_compiled = transpile(qc, self.simulator)

        job_sim = self.simulator.run(qc_compiled, shots=self.conf.total_shots)
        result_sim = job_sim.result()
        counts_sim = result_sim.get_counts(qc_compiled)

        counts_sim = {k.removeprefix('00 '): v for k, v in counts_sim.items()}

        self.analyzer.hist(counts_sim, name, self.p_dephase)

        return counts_sim


    def _run_sampler(self, qc_transpiled):
        job = self.sampler.run([qc_transpiled], shots=self.conf.total_shots)

        result = job.result()
        counts = result._pub_results[0].data.c.get_counts()
        
        # Assuming 'counts' is a dictionary of measurement outcomes from the raw sampler
        total_counts = sum(counts.values())
        probabilities = {state: count / total_counts for state, count in counts.items()}

        # Construct the density matrix
        rho = DensityMatrix.from_label('00')  # Initialize with an arbitrary state
        for state, prob in probabilities.items():
            rho += prob * DensityMatrix.from_label(state)

        return counts, rho


    def _run_estimator(self, qc_transpiled, op_str, op1, op2):
        num_qubits_transpiled = qc_transpiled.num_qubits
        op_expanded = SparsePauliOp.from_list([(op_str + "I" * (num_qubits_transpiled - len(op_str)), op1),
                                            ("I" * num_qubits_transpiled, op2)])

        pub = (qc_transpiled, [op_expanded], None)
        job = self.estimator.run([pub])
        return job.result()


    def exec(self, conf, results: Results):
        counts_list = []
        legend = []
        colors = []

        for obs in self.observables:
            observable = obs["observable"]

            qc, qc_transpiled = self._qet_circuit(obs, observable.num_qubits)

            if conf.run_simulator:
                self.analyzer.add_section('Simulator')
                counts_sim = self._run_sim(qc, obs.name)
                
                expectation_sim = self.analyzer.calc_expectation(obs, counts_sim, self.conf.total_shots)
                self.analyzer.print_expectation(expectation_sim, counts_sim, self.p_dephase, obs)
                
                counts_list.append(counts_sim)
                legend.append('Simulator')
                colors.append('crimson')
                
                results.add_result('simulator', self.conf.h, self.conf.k, self.p_dephase, counts_sim, expectation_sim, obs)

            if conf.run_sampler:
                self.analyzer.add_section(f'Sampler with backend {self.backend.name}')

                counts_hw, rho = self._run_sampler(qc_transpiled)
                
                self.analyzer.print_rho(rho, obs)

                expectation_hw = self.analyzer.calc_expectation(obs, counts_hw, self.conf.total_shots)
                self.analyzer.print_expectation(expectation_hw, counts_hw, self.p_dephase, obs)
                
                counts_list.append(counts_hw)
                legend.append('Raw Sampler')
                colors.append('midnightblue')
                
                results.add_result('sampler', self.conf.h, self.conf.k, self.p_dephase, counts_hw, expectation_hw, obs)

        self.analyzer.add_section(f'Summary histograms')
        self.analyzer.create_histogram(counts_list, legend, colors, self.conf.total_shots, self.p_dephase, obs)
