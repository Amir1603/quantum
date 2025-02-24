from analysis import Analyzer
from conf import Conf
from qiskit_aer import Aer, AerSimulator
from qiskit_aer.noise import NoiseModel, phase_damping_error
from qiskit import QuantumCircuit, transpile
from qiskit.circuit import ClassicalRegister, Delay
from qiskit.quantum_info import SparsePauliOp, DensityMatrix
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2, EstimatorV2
import numpy as np


class Runner():

    def __init__(self, conf: Conf):
        self.h = conf.h
        self.k = conf.k
        self.total_shots = conf.total_shots
        self.noise_model = None

        self.h1 = SparsePauliOp.from_list([("ZI", conf.h), ("II", conf.h**2 / np.sqrt(conf.h**2 + conf.k**2))])
        self.v = SparsePauliOp.from_list([("XX", 2 * conf.k), ("II", 2 * conf.k**2 / np.sqrt(conf.h**2 + conf.k**2))])

        self.analyzer = None
        self.service = QiskitRuntimeService()

        Analyzer.save_conf(conf)


    def __choose_backend(self, backend_name):
        if self.noise_model:
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
        self.analyzer = Analyzer(self.h, self.k, self.p_dephase, self.backend.name)

        self.estimator = None if self.noise_model else EstimatorV2(mode=self.backend)
        self.sampler = SamplerV2(mode=self.backend)


    def finalize_run(self):
        self.analyzer.generate_html_report()


    def wrap():
        Analyzer.dump_confs()


    def _qet_circuit(self, apply_h,  num_qubits, name):
        """
        Constructs the quantum circuit for the QET experiment.

        Args:
        apply_h: Bool indicating wether to apply hadmard gate.
        num_qubits: The number of qubits for the circuit.
        name: The classical register name.

        Returns:
        qc: The constructed QuantumCircuit object.
        qc_transpiled: The transpiled quantum circuit object.
        """
        
        delay_time = 10000
        delay = Delay(delay_time)

        qc = QuantumCircuit(2, 2)
        qc.name = f'{name}_qc'

        # Prepare the ground state
        theta = -np.arccos(
            (1 / np.sqrt(2)) * np.sqrt(1 - self.h / np.sqrt(self.h**2 + self.k**2))
        )
        qc.ry(2 * theta, 0)
        qc.cx(0, 1)

        qc.h(0)
        
        # Alice's measurement
        qc.measure(0, 0)  # Measure qubit 0 into classical bit 0

        # Idle Bob’s qubit before he acts
        qc.append(delay, [1])

        # Bob's conditional operation
        phi = np.arcsin(
            (self.h * self.k) / np.sqrt((self.h**2 + 2 * self.k**2)**2 + self.h**2 * self.k**2)
        ) / 2

        # Bob's conditional operation
        qc.ry(2 * phi, 1).c_if(0, 0)  # Apply U(+1) if classical bit 0 is 0
        qc.ry(-2 * phi, 1).c_if(0, 1)  # Apply U(-1) if classical bit 0 is 1

        if apply_h:
            qc.h(1)

        qc.measure(1, 1)  # Measure qubit 1 into classical bit 1

        cr = ClassicalRegister(num_qubits, name)
        qc.add_register(cr)  # Add the ClassicalRegister
        qc_transpiled = transpile(qc, self.backend)

        self.analyzer.draw_circuit(qc)

        return qc, qc_transpiled


    def _create_noise_model(self):
        # Create dephasing error
        dephase_error = phase_damping_error(self.p_dephase)

        # Build the noise model
        noise_model = NoiseModel()
        noise_model.add_all_qubit_quantum_error(dephase_error, ['id', 'measure'])  # Affect idling and measurement steps

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
        simulator = Aer.get_backend('qasm_simulator')
        qc_compiled = transpile(qc, simulator)

        job_sim = simulator.run(qc_compiled, shots=self.total_shots)
        result_sim = job_sim.result()
        counts_sim = result_sim.get_counts(qc_compiled)

        counts_sim = {k.removeprefix('00 '): v for k, v in counts_sim.items()}

        self.analyzer.hist(counts_sim, name, self.p_dephase)

        return counts_sim


    def _run_sampler(self, qc_transpiled):
        job = self.sampler.run([qc_transpiled], shots=self.total_shots)

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


    def exec(self, conf):
        qc_h1, qc_h1_transpiled = self._qet_circuit(False, self.h1.num_qubits, 'h1')
        qc_v, qc_v_transpiled = self._qet_circuit(True, self.v.num_qubits, 'v')

        h1_counts_list = []
        v_counts_list = []
        legend = []
        colors = []

        if conf.run_simulator:
            self.analyzer.add_section('Simulator')
            h1_counts_sim = self._run_sim(qc_h1, "H1")
            v_counts_sim = self._run_sim(qc_v, "V")
            
            self.analyzer.print_expectations(h1_counts_sim, v_counts_sim, self.total_shots, self.p_dephase)
            h1_counts_list.append(h1_counts_sim)
            v_counts_list.append(v_counts_sim)
            legend.append('Simulator')
            colors.append('crimson')

        if conf.run_sampler:
            self.analyzer.add_section(f'Sampler with backend {self.backend.name}')

            h1_counts_hw, h1_rho = self._run_sampler(qc_h1_transpiled)
            v_counts_hw, v_rho = self._run_sampler(qc_v_transpiled)
            
            self.analyzer.print_rho(h1_rho, v_rho)

            self.analyzer.print_expectations(h1_counts_hw, v_counts_hw, self.total_shots, self.p_dephase)
            h1_counts_list.append(h1_counts_hw)
            v_counts_list.append(v_counts_hw)
            legend.append('Raw Sampler')
            colors.append('midnightblue')

        if conf.run_estimator:
            self.analyzer.add_section(f'Estimator with backend {self.backend.name}')

            if conf.error_mitigation:
                self._prep_error_mitigation()

            result_h1 = self._run_estimator(qc_h1_transpiled, "Z", op1=self.h, op2=self.h**2 / np.sqrt(self.h**2 + self.k**2))
            result_v = self._run_estimator(qc_v_transpiled, "XX", op1=2*self.k, op2=2 * self.k**2 / np.sqrt(self.h**2 + self.k**2))
            self.analyzer.print_results(result_h1, result_v)

        self.analyzer.add_section(f'Summary histograms')
        self.analyzer.create_histograms(h1_counts_list, v_counts_list, legend, colors, self.total_shots, self.p_dephase)
