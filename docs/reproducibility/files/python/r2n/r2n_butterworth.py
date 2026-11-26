import numpy as np
from scipy.signal import butter, lfilter


def r2n_butterworth(x, kind, order, fc, fs):
    """ros2neuro_filters_butterworth: causal IIR Butterworth (low-pass or high-pass), run over the whole signal.

    x : [samples, channels]; kind : 'low' | 'high'; order, fc (Hz), fs (Hz).
    scipy: butter designs the filter and lfilter runs it causally, in double precision, the state going on across the whole signal:
    the same as the plugin, which filters frame after frame with the state kept (double) and publishes float32.
    Returns y (float32) and the coefficients b, a.
    """
    if kind.lower() not in ('low', 'high'):
        raise ValueError('kind must be "low" or "high"')
    b, a = butter(order, fc / (fs / 2), btype=kind.lower())
    return lfilter(b, a, np.asarray(x, dtype=np.float64), axis=0).astype(np.float32), b, a
