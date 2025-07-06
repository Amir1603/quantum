from qiskit import QuantumCircuit
from enum import Enum
import numpy as np
from scipy.sparse import kron, csc_matrix


class System(Enum):
    AliceInteraction = 'Alice'
    NearestNeighborInteraction = 'NearestNeighbors'

    def __str__(self):
        return self.value


class AliceBase(Enum):
    X = 'X'
    Y = 'Y'

    def __str__(self):
        return self.value

def get_nested_value(data, path_str):
    """
    Retrieves a value from a nested dictionary or object using a dot-separated path.

    Args:
        data (dict or object): The data structure to traverse.
        path_str (str): Dot-separated path to the desired value.

    Returns:
        The value at the specified path, or None if the path is invalid.
    """
    current_val = data
    try:
        for key in path_str.split('.'):
            if isinstance(current_val, dict):
                current_val = current_val[key]
            else:
                current_val = getattr(current_val, key)
        return current_val
    except (KeyError, AttributeError, TypeError, IndexError):
        return None

def get_alice_idx(N):
    return 0

def get_bob_idx(N):
    return N

def get_bob_neighbor_idx(N):
    return get_bob_idx(N) - 1

def get_bit_from_counts(bitstring: str, creg_index: int, num_clbits: int) -> str:
    """
    Safely extracts the bit value ('0' or '1') from a Qiskit counts bitstring
    based on the classical register index.

    Args:
        bitstring (str): The bitstring key from the counts dictionary (e.g., '101').
        creg_index (int): The index of the classical register whose value is needed (e.g., 0, 1, 2).
        num_clbits (int): The total number of classical bits in the circuit
                          that generated this bitstring.

    Returns:
        str: The bit value ('0' or '1') corresponding to the specified classical register.

    Raises:
        IndexError: If the calculated bitstring index is out of bounds or
                    if the bitstring length doesn't match num_clbits.
    """
    if len(bitstring) != num_clbits:
        # Handle potential formatting issues, like spaces sometimes present in old Qiskit versions
        cleaned_bitstring = bitstring.replace(' ', '')
        if len(cleaned_bitstring) == num_clbits:
            bitstring = cleaned_bitstring # Use cleaned version if length matches
        else:
            raise IndexError(
                f"Bitstring '{bitstring}' length ({len(bitstring)}) "
                f"does not match expected number of classical bits ({num_clbits})."
            )

    # Qiskit orders bitstrings with classical bit 0 (c0) on the right.
    # Example: For 3 clbits (c2, c1, c0), the string is 'c2c1c0'.
    # Index in string = num_clbits - 1 - creg_index
    string_index = num_clbits - 1 - creg_index

    if string_index < 0 or string_index >= len(bitstring):
        raise IndexError(
            f"Calculated string index {string_index} is out of bounds for "
            f"bitstring '{bitstring}' (creg_index={creg_index}, num_clbits={num_clbits})."
        )

    return bitstring[string_index]

def apply_basis(qc: QuantumCircuit, basis: str, site_idx: int):
    basis = str(basis)
    if basis == "X":
        qc.h(site_idx)
    elif basis == "Y":
        qc.sdg(site_idx) # Apply S dagger
        qc.h(site_idx)
    elif basis == "Z":
        pass # For measuting Z we do nothing
    else:
        raise ValueError(f"Unknown measurement basis {basis} for Bob!")

# Pauli Matrices
I = csc_matrix(np.array([[1, 0], [0, 1]], dtype=complex))
X = csc_matrix(np.array([[0, 1], [1, 0]], dtype=complex))
Y = csc_matrix(np.array([[0, -1j], [1j, 0]], dtype=complex))
Z = csc_matrix(np.array([[1, 0], [0, -1]], dtype=complex))
pauli_ops = {'I': I, 'X': X, 'Y': Y, 'Z': Z}

# Helper function to create a Pauli operator on a specific site
def get_pauli_operator_on_site(op_char: str, site_idx: int, N: int):
    # We reverse the indices because the kron product builds operators from left to right,
    # which means the leftmost operator acts on the most significant qubit.
    site_idx = N - site_idx

    # pauli_ops is a dict {'I': I_op, 'X': X_op, ...}
    if not (0 <= site_idx <= N):
        raise ValueError(f"Site index {site_idx} out of bounds for N={N}")

    op_list = [pauli_ops[op_char] if i == site_idx else pauli_ops['I'] for i in range(N+1)]

    full_operator = op_list[0]
    for i_op in range(1, N+1):
        full_operator = kron(full_operator, op_list[i_op], format="csc")

    return full_operator

# Helper function for multi-site operators like X_i Z_j or X_i X_j Z_k
def get_multi_site_operator(ops_tuple_list, N: int):
    # We reverse the indices because the kron product builds operators from left to right,
    # which means the leftmost operator acts on the most significant qubit.
    op_tuple_list = [(pauli_ops[char], N - idx) for char, idx in ops_tuple_list]

    # Starting from identity operator on all sites
    op_list = [pauli_ops['I']] * (N+1)

    for op, site in op_tuple_list:
        op_list[site] = op_list[site] @ op

    full_operator = op_list[0]
    for i_op in range(1, N+1):
        full_operator = kron(full_operator, op_list[i_op], format="csc")

    return full_operator
