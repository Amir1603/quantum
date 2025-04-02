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

def get_bob_qubit_idx(N):
    return N - 1

def get_counts_alice_qubit_idx(N):
    # Because we have only two measurements, for Alice & Bob,
    # the index for the counts result is still 1
    return 1

def get_counts_bob_qubit_idx(N):
    return 0