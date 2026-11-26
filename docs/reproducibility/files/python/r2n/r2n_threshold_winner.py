import numpy as np


def r2n_threshold_winner(thresholds, values):
    """ros2neuro_control_feedback: the class over its own threshold (value + 1e-6 >= threshold, in float32).
    The highest value wins when several are over; returns its 0-based index, -1 = none. Used to recompute Hit / Miss / Timeout."""
    w = -1
    th = np.asarray(thresholds, dtype=np.float32)
    values = np.asarray(values, dtype=np.float32)
    for i in range(len(th)):
        if values[i] + np.float32(1e-6) < th[i]:
            continue
        if w < 0 or values[i] > values[w]:
            w = i
    return w
