"""Writes the parameter file of fbcsp_node from CSP matrices trained anywhere (MNE, scikit-learn, your own code).

    from write_fbcsp_yaml import write_fbcsp_yaml
    write_fbcsp_yaml("fbcsp.yaml", channels, bands, W, fs=512, window=512)

channels  labels of the channels W was trained on, in the order of the rows of W (they must be in the frames, labels as the acquisition gives them)
bands     [(low_hz, high_hz), ...] the band-pass of every band
W         one array [channels x components] per band: the spatial filters, as columns (component k of the band = W[:, k])
fs        sample rate of the data the filters are applied to
window    samples the variance is computed on

The band-pass of a band is a high-pass and a low-pass Butterworth of `order`, the same two sections train_fbcsp.m uses. If your bands are
filtered in another way, give the coefficients instead: replace the four lists of a band with your own b and a (a[0] must be 1).
"""
import numpy as np
from scipy import signal


def _num(v):
    t = repr(float(v))                       # always a decimal point: ROS reads a list of doubles, not of integers
    return t


def _vec(values):
    return "[" + ", ".join(_num(v) for v in np.asarray(values, dtype=float).ravel()) + "]"


def write_fbcsp_yaml(path, channels, bands, W, fs, window, order=2):
    if len(bands) != len(W):
        raise ValueError("one W per band")
    components = np.asarray(W[0]).shape[1]
    for w in W:
        if np.asarray(w).shape != (len(channels), components):
            raise ValueError("every W must be [channels x components]")
    lines = ["fbcsp:", "  ros__parameters:",
             "    channels: [" + ", ".join(f'"{c}"' for c in channels) + "]",
             f"    window: {int(window)}", f"    components: {int(components)}", f"    n_bands: {len(bands)}"]
    for b, ((low, high), w) in enumerate(zip(bands, W), start=1):
        bh, ah = signal.butter(order, low, btype="highpass", fs=fs)
        bl, al = signal.butter(order, high, btype="lowpass", fs=fs)
        lines += [f"    band_{b}.centre: {_num((low + high) / 2)}",
                  f"    band_{b}.hp_b: {_vec(bh)}", f"    band_{b}.hp_a: {_vec(ah)}",
                  f"    band_{b}.lp_b: {_vec(bl)}", f"    band_{b}.lp_a: {_vec(al)}",
                  f"    band_{b}.w: {_vec(np.asarray(w).ravel())}"]       # row-major [channels x components]
    with open(path, "w") as f:
        f.write("\n".join(lines) + "\n")
