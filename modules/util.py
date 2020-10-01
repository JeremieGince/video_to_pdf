import numpy as np


def is_array_in_set(array_set, array: np.ndarray) -> bool:
    is_in = False
    for a in array_set:
        if np.allclose(a, array):
            is_in = True
            break
    return is_in


def is_array_in_set_at(array_set, array: np.ndarray, idx: int, threshold: float = 0.1):
    if len(array_set) == 0:
        return False
    return mse(array_set[idx], array) < threshold


def mse(a: np.ndarray, b: np.ndarray):
    return np.mean((a - b)**2)