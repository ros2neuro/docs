import numpy as np

from r2n_r2nd import R2ndReader


def r2n_gaussian_read(file):
    """Reads the .r2nd file of the Gaussian decoder (GaussianModel.cpp, version 2, little endian).

    Returns a dict: priors, frequencies, selection_channel / selection_frequency (0-based), prototypes, centers [S, prototypes, K],
    covariances [S, prototypes, K], n_classes.
    """
    r = R2ndReader(file)
    if r.version != 2:
        raise ValueError('unsupported .r2nd version')
    for _ in range(4):
        r.string()                                          # name, subject, type, parameterization
    m = {'priors': r.float_list()}
    r.regularization()
    for _ in range(4):
        r.string()                                          # solver, source, feature name, unit
    r.u8(); r.u8()                                          # feature type, output type
    n_ch, n_fr, n_sel, n_cl = (r.u32() for _ in range(4))
    m['prototypes'] = r.u32()
    for _ in range(n_ch):
        r.string()
    m['frequencies'] = r.f32(n_fr)
    sel = r.u32s(2 * n_sel).reshape(n_sel, 2)
    m['selection_channel'], m['selection_frequency'] = sel[:, 0], sel[:, 1]           # 0-based
    for _ in range(n_cl):
        r.string()
    n = n_cl * m['prototypes'] * n_sel
    shape = (n_cl, m['prototypes'], n_sel)                  # stored class after class, prototype after prototype
    m['centers'] = r.f32(n).reshape(shape).transpose(2, 1, 0)
    m['covariances'] = r.f32(n).reshape(shape).transpose(2, 1, 0)
    m['n_classes'] = n_cl
    return m
