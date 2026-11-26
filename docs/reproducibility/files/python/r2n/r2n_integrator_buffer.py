import numpy as np


def r2n_integrator_buffer(prob, buffer_size, increment, reset_frames=(), init_val=None):
    """ros2neuro_integrator_buffer (Buffer.cpp) in float32.

    prob : [frames, K] decoder output; buffer_size : the steps to go from 0 to 1; increment : 0 hard (step 1/buffer_size) or 1 soft
    (step = winning value / buffer_size); reset_frames : frames (0-based) at which the buffer goes back to its reset state before
    the frame is integrated; init_val : the reset state (normalized to sum 1; default the uniform 1/K). The buffer starts from it.
    Per frame the class with the highest value (the first one on a tie) goes up by the step (at most to 1) and the same amount is
    taken from the others in equal shares; a class that would go below 0 stops at 0 and the rest of its share goes to the others.
    """
    f32 = np.float32
    nframes, K = prob.shape
    if init_val is None:
        start = np.full(K, 1 / K, dtype=f32)
    else:
        iv = np.asarray(init_val, dtype=f32).astype(np.float64)
        start = (iv / iv.sum()).astype(f32)
    prob = np.asarray(prob, dtype=f32)
    y = np.zeros((nframes, K), dtype=f32)
    data = start.copy()
    resets = set(reset_frames)
    for f in range(nframes):
        if f in resets:
            data = start.copy()
        w = int(np.argmax(prob[f]))
        step = f32(1) / f32(buffer_size) if increment == 0 else f32(prob[f, w] / f32(buffer_size))
        gain = min(step, f32(f32(1) - data[w]))
        data[w] = f32(data[w] + gain)
        remaining = gain
        while remaining > f32(1e-9):
            active = [i for i in range(K) if i != w and data[i] > 0]
            if not active:
                break
            share = f32(remaining / f32(len(active)))
            for i in active:
                taken = min(data[i], share)
                data[i] = f32(data[i] - taken)
                remaining = f32(remaining - taken)
        y[f] = data
    return y
