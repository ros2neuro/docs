import numpy as np


def r2n_fbcsp(window, W):
    """ros2neuro_processing_fbcsp (FbcspCore.h): the FBCSP feature of one analysis window, from bands that are ALREADY band-passed.

    window : list with one [buffer, channels] array per band (the last `buffer` samples of the signal of that band, i.e. the output of
    the filter chain of the band: hp at lo then lp at hi, see r2n_butterworth); W : [bands, components, channels] CSP filters
    (r2n_fbcsp_weights). Per band, in double: z = x @ W[b].T (every component), v = population variance of z (mean removed), the
    feature of component k is log(max(v_k / sum_j v_j, 1e-12)) (0 if the total is 0). Returns the feature as a vector, band-major
    (index = band * components + component), float32 like the published feature.
    """
    comps = W.shape[1]
    f = np.zeros(len(window) * comps)
    for b, x in enumerate(window):
        z = np.asarray(x, dtype=np.float64) @ W[b].T
        v = z.var(axis=0)                                   # population variance (ddof=0) of every component
        total = v.sum()
        frac = v / total if total > 0 else np.zeros(comps)
        f[b * comps:(b + 1) * comps] = np.log(np.maximum(frac, 1e-12))
    return f.astype(np.float32)
