from conf import Conf
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import SparsePauliOp


class Observable:
    def __init__(self, name, expression):
        self.name = name
        self.expression = expression


    def is_positive_count(key):
        raise NotImplementedError()


    def apply_gate_on_qc(qc: QuantumCircuit):
        raise NotImplementedError()
    

    def description():
        return "Abstract Observable"


class H1(Observable):
    def __init__(self, conf: Conf):
        super().__init__("h1", SparsePauliOp.from_list([("ZI", conf.h), ("II", conf.h**2 / np.sqrt(conf.h**2 + conf.k**2))]))


    def is_positive_count(key):
        return key[1] == '0' # Check the second bit for <H1>


    def apply_gate_on_qc(qc: QuantumCircuit):
        pass


    def description():
        return "Z (H1)"


class V(Observable):
    def __init__(self, conf: Conf):
        super().__init__("v", SparsePauliOp.from_list([("XX", 2 * conf.k), ("II", 2 * conf.k**2 / np.sqrt(conf.h**2 + conf.k**2))]))

    
    def is_positive_count(key):
        return key in ('11', '00')
    

    def apply_gate_on_qc(qc: QuantumCircuit):
        qc.h(1)

    
    def description():
        return "XX (V)"


def create_observables(conf: Conf) -> list[Observable]:
        return [H1(conf), V(conf)]