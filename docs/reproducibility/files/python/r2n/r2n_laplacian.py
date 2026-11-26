import numpy as np


def r2n_laplacian(x, layout):
    """ros2neuro_filters_laplacian: y = x @ mask. Column c of the mask has +1 on channel c and -1/n on each of its n neighbours
    (left, right, up, down in the grid of the layout, where there is an electrode; 0 = no electrode).

    x : [samples, channels]; layout : 2-D array such as [[1, 2, 3], [4, 5, 6], [7, 8, 9]] (channel numbers, 1-based) or the text of
    the yaml parameter "1 2 3; 4 5 6; 7 8 9". The product is numpy's, in float32 (a few ULP of difference at most).
    """
    x = np.asarray(x, dtype=np.float32)
    nch = x.shape[1]
    if isinstance(layout, str):
        layout = [[int(v) for v in row.split()] for row in layout.split(';') if row.strip()]
    layout = np.asarray(layout, dtype=int)
    nr, nc = layout.shape
    mask = np.zeros((nch, nch))
    for ch in range(1, nch + 1):
        where = np.argwhere(layout == ch)
        if len(where) == 0:
            continue
        r, c = where[0]
        nb = []
        if c > 0 and layout[r, c - 1]:
            nb.append(layout[r, c - 1])
        if c < nc - 1 and layout[r, c + 1]:
            nb.append(layout[r, c + 1])
        if r > 0 and layout[r - 1, c]:
            nb.append(layout[r - 1, c])
        if r < nr - 1 and layout[r + 1, c]:
            nb.append(layout[r + 1, c])
        mask[ch - 1, ch - 1] = 1
        for n in nb:
            mask[n - 1, ch - 1] = -1 / len(nb)
    return x @ mask.astype(np.float32)
