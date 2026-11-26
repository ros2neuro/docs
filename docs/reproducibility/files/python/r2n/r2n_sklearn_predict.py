import numpy as np


def r2n_sklearn_predict(m, feature, labels=None, values=None):
    """The probabilities of a scikit-learn model (r2n_sklearn_load) for ONE feature, as ros2neuro_decoder_sklearn publishes them.

    m : dict of r2n_sklearn_load; feature : the NeuroFeature as a 2-D array [axis 0, axis 1] (PSD: [channels, frequencies]; FBCSP:
    [bands, components]); labels, values : the labels of the channels (or bands) and the frequency values of the feature, if it does
    not have the axes of the manifest in their order (it is then reordered by label / value, like the plugin; missing ones are an error).
    The feature is taken as the model was fitted on (all of it, axis 0 major, or the selected pairs), in double; the result is the
    probability of every class in the order of `m['classes']`, float32.
    """
    data = np.asarray(feature, dtype=np.float32)
    if labels is not None and m['axes'][0]['labels']:
        data = np.take(data, [[str(v) for v in labels].index(c) for c in m['axes'][0]['labels']], axis=0)
    if values is not None and m['axes'][1]['values']:
        data = np.take(data, [int(np.argmin(np.abs(np.asarray(values, dtype=float) - v))) for v in m['axes'][1]['values']], axis=1)
    if m['mode'] == 'selection':
        x = np.array([data[i, j] for i, j in m['selection']], dtype=np.float64)
    else:
        x = data.reshape(-1).astype(np.float64)
    p = m['model'].predict_proba(x.reshape(1, -1))[0]
    return np.array([p[i] for i in m['class_index']], dtype=np.float32)
