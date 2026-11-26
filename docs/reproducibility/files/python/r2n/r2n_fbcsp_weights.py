import numpy as np


def r2n_fbcsp_weights(filters, bands, components, channels):
    """The CSP filters of the parameter `filters` of the Fbcsp plugin (a flat list, [band][component][channel], channel varying
    fastest) as the [bands, components, channels] array r2n_fbcsp takes."""
    return np.asarray(filters, dtype=np.float64).reshape(bands, components, channels)
