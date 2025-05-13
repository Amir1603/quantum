from functools import reduce
import operator

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

def get_alice_qubit_idx(N):
    return 0

def get_bob_neighbor_qubit_idx(N):
    return N - 2

def get_bob_qubit_idx(N):
    return N - 1

def get_counts_alice_creg_idx(N):
    return 0

def get_counts_bob_creg_idx(N):
    return 1

def get_counts_alice_qubit_idx(N):
    # Because we have only two measurements, for Alice & Bob,
    # the index for the counts result is still 1
    return 1

def get_counts_bob_qubit_idx(N):
    return 0

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

def get_counts_intermediate_creg_idx(N):
     """
     Returns the classical register index used for measuring the
     intermediate qubit (site 1) when N=3.
     Returns None if N is not 3.
     """
     if N != 3:
          # Or raise ValueError("Intermediate qubit only defined for N=3")
          return None
     # Based on convention: Alice=c0, BobZ2=c1, IntermedZ1=c2
     return 2
