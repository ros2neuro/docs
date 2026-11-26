from r2n_r2nd import R2ndReader


def r2n_linear_read(file):
    """Reads the .r2nd of the LDA or the SVM decoder (LDAModel.cpp / SVMModel.cpp: the same layout, version 1 or 2, little endian).

    Returns a dict: type, parameterization, classes, channels, frequencies, selection_channel / selection_frequency (0-based),
    weights [K, S] (one row per class), bias [K], n_classes.
    """
    r = R2ndReader(file)
    if r.version not in (1, 2):
        raise ValueError('unsupported .r2nd version')
    r.string(); r.string()                                  # name, subject
    m = {'type': r.string(), 'parameterization': r.string()}
    if r.version >= 2:
        r.float_list()                                      # priors (not used by the prediction)
        r.regularization()
        r.string(); r.string()                              # solver, source
    r.string(); r.string(); r.u8(); r.u8()                  # feature name, unit, feature type, output type
    n_ch, n_fr, n_sel, n_cl = (r.u32() for _ in range(4))
    m['channels'] = [r.string() for _ in range(n_ch)]
    m['frequencies'] = r.f32(n_fr)
    sel = r.u32s(2 * n_sel).reshape(n_sel, 2)
    m['selection_channel'], m['selection_frequency'] = sel[:, 0], sel[:, 1]           # 0-based
    m['classes'] = [r.string() for _ in range(n_cl)]
    m['weights'] = r.f32(n_cl * n_sel).reshape(n_cl, n_sel)           # stored one class after the other
    m['bias'] = r.f32(n_cl)
    m['n_classes'] = n_cl
    return m
