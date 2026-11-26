from r2n_r2nd import R2ndReader


def r2n_qda_read(file):
    """Reads the .r2nd of the QDA decoder (QDAModel.cpp, version 2, little endian).

    Returns a dict: type, parameterization, classes, channels, frequencies, selection_channel / selection_frequency (0-based),
    linear [K, S], quadratic [K, S, S] (quadratic[k][row, col] as in the C++), bias [K], n_classes.
    """
    r = R2ndReader(file)
    if r.version != 2:
        raise ValueError('unsupported .r2nd version')
    r.string(); r.string()                                  # name, subject
    m = {'type': r.string(), 'parameterization': r.string()}
    r.float_list()                                          # priors (not used by the prediction)
    r.regularization()
    for _ in range(4):
        r.string()                                          # solver, source, feature name, unit
    r.u8(); r.u8()                                          # feature type, output type
    n_ch, n_fr, n_sel, n_cl = (r.u32() for _ in range(4))
    m['channels'] = [r.string() for _ in range(n_ch)]
    m['frequencies'] = r.f32(n_fr)
    sel = r.u32s(2 * n_sel).reshape(n_sel, 2)
    m['selection_channel'], m['selection_frequency'] = sel[:, 0], sel[:, 1]           # 0-based
    m['classes'] = [r.string() for _ in range(n_cl)]
    m['linear'] = r.f32(n_cl * n_sel).reshape(n_cl, n_sel)
    m['quadratic'] = r.f32(n_cl * n_sel * n_sel).reshape(n_cl, n_sel, n_sel)          # row-major on file
    m['bias'] = r.f32(n_cl)
    m['n_classes'] = n_cl
    return m
