import numpy as np


def r2n_softmax(score):
    """The probabilities of the LDA, QDA and SVM decoders: exp(score - max) in float32, divided by their sum (added in order).
    If the sum is not above eps(float32) the values are returned as they are (the C++ does the same)."""
    score = np.asarray(score, dtype=np.float32)
    raw = np.exp(score - score.max()).astype(np.float32)
    s = np.float32(0)
    for v in raw:
        s = np.float32(s + v)
    return raw if s <= np.finfo(np.float32).eps else (raw / s).astype(np.float32)
