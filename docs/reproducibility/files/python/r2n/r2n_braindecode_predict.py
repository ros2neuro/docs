import numpy as np


def r2n_braindecode_predict(m, windows, buffer_labels=None):
    """The probabilities of a deep-learning model (r2n_braindecode_load) for a batch of windows, as ros2neuro_decoder_braindecode
    publishes them.

    m : dict of r2n_braindecode_load; windows : [n, samples, channels] (the Buffer feature: the last `samples` samples of the filtered
    signal); buffer_labels : the labels of its channels, to pick the ones the network reads by label, in its order (default: the
    windows already have those channels). The network gets [n, channels, samples] float32 on the CPU. If it outputs log-probabilities
    (its exp sums to 1) they are exponentiated, else a softmax is applied. Returns [n, K] float64 in the order of m['fields'].
    """
    import torch
    windows = np.asarray(windows, dtype=np.float32)
    if buffer_labels is not None:
        windows = windows[:, :, [list(buffer_labels).index(c) for c in m['labels']]]
    with torch.no_grad():
        out = m['net'](torch.tensor(windows.transpose(0, 2, 1))).double()
        p = torch.exp(out)
        return (p if abs(float(p.sum(1).mean()) - 1.0) < 1e-4 else torch.softmax(out, dim=1)).numpy()
