import numpy as np


def r2n_car(x):
    """ros2neuro_filters_car: common average reference. y[s, :] = x[s, :] - mean(x[s, :]).

    x : [samples, channels]. Returns float32. numpy adds the channels in a different order from Eigen: a few ULP of difference at most.
    """
    x = np.asarray(x, dtype=np.float32)
    return x - x.mean(axis=1, keepdims=True, dtype=np.float32)
