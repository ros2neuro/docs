import numpy as np


def r2n_gaussian_predict(m, feature):
    """ros2neuro_decoder_gaussian (Gaussian.cpp) in float32: the probability of every class for one PSD feature.

    m : dict of r2n_gaussian_read; feature : the feature, channel-major (all channels x all frequencies of the model), 1-D.
    Per class the log-sum-exp over the prototypes of sum(-0.5 d^2/v - 0.5 ln v), plus ln(prior); exp(score - max), divided by the sum.
    """
    f32 = np.float32
    nfreq = len(m['frequencies'])
    x = np.asarray(feature, dtype=f32).ravel()[m['selection_channel'] * nfreq + m['selection_frequency']]
    score = np.zeros(m['n_classes'], dtype=f32)
    for k in range(m['n_classes']):
        act = np.zeros(m['prototypes'], dtype=f32)
        for q in range(m['prototypes']):
            d = x - m['centers'][:, q, k]
            v = m['covariances'][:, q, k]
            a = f32(0)
            for j in range(len(x)):
                a = f32(a + f32(f32(-0.5) * f32(f32(d[j] * d[j]) / v[j]) - f32(0.5) * np.log(v[j])))
            act[q] = a
        mx = act.max()
        e = np.exp(act - mx).astype(f32)
        total = f32(0)
        for v in e:
            total = f32(total + v)
        s = f32(mx + np.log(total))
        if len(m['priors']) and m['priors'][k] > 0:
            s = f32(s + np.log(m['priors'][k]))
        score[k] = s
    raw = np.exp(score - score.max()).astype(f32)
    total = f32(0)
    for v in raw:
        total = f32(total + v)
    return (raw / total).astype(f32)
