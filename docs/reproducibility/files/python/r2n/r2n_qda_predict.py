import numpy as np

from r2n_softmax import r2n_softmax


def r2n_qda_predict(m, feature):
    """ros2neuro_decoder_qda (QDA.cpp) in float32.

    m : dict of r2n_qda_read; feature : the PSD feature, channel-major (all channels x all frequencies of the model), 1-D.
    score_k = bias_k + sum_i l_ki x_i + sum_row sum_col x_row q_k(row, col) x_col (added in this order), then exp(score - max) / sum.
    Returns the probabilities and the scores.
    """
    f32 = np.float32
    nfreq = len(m['frequencies'])
    x = np.asarray(feature, dtype=f32).ravel()[m['selection_channel'] * nfreq + m['selection_frequency']]
    S = len(x)
    score = np.zeros(m['n_classes'], dtype=f32)
    for k in range(m['n_classes']):
        s = m['bias'][k]
        for i in range(S):
            s = f32(s + f32(m['linear'][k, i] * x[i]))
        q = m['quadratic'][k]
        for r in range(S):
            for c in range(S):
                s = f32(s + f32(f32(x[r] * q[r, c]) * x[c]))
        score[k] = s
    return r2n_softmax(score), score
