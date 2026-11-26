import numpy as np

from r2n_softmax import r2n_softmax


def r2n_linear_predict(m, feature):
    """ros2neuro_decoder_lda (LDA.cpp) and ros2neuro_decoder_svm (SVM.cpp) in float32: the same arithmetic.

    m : dict of r2n_linear_read; feature : the PSD feature, channel-major (all channels x all frequencies of the model), 1-D.
    score_k = bias_k + sum_i w_ki x_i (added in the order of the selection), then exp(score - max) / sum (TYPE_PROBABILITIES).
    Returns the probabilities and the scores (what the node publishes for a model with TYPE_SCORES).
    """
    nfreq = len(m['frequencies'])
    x = np.asarray(feature, dtype=np.float32).ravel()[m['selection_channel'] * nfreq + m['selection_frequency']]
    score = np.zeros(m['n_classes'], dtype=np.float32)
    for k in range(m['n_classes']):
        s = m['bias'][k]
        for i in range(len(x)):
            s = np.float32(s + np.float32(m['weights'][k, i] * x[i]))
        score[k] = s
    return r2n_softmax(score), score
