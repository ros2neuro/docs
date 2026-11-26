import numpy as np


def r2n_integrator_exponential(prob, alpha, reset_frames=(), first=0, hop=1, fs=1):
    """ros2neuro_integrator_exponential: state = alpha * state + (1 - alpha) * prediction, in float32.

    prob : [frames, K] decoder output (float32, NaN before frame `first`); alpha : smoothing (0..1); reset_frames : the frames (0-based)
    at which the state goes back to 1/K (the integrator's reset event or the /reset service); first : first frame with a prediction;
    hop, fs : samples per frame and sampling rate, only to return the time of every reset.
    The first prediction of the run becomes the state; at a reset the state is all 1/K and the frame is integrated from there.
    ROS integrates the frame that contains the event and resets after it (the caller passes ceil(position / hop) + 1, 0-based).
    Returns y [frames, K] and the times of the resets.
    """
    f32 = np.float32
    nframes, K = prob.shape
    y = np.full((nframes, K), np.nan, dtype=f32)
    state, reset_t = None, []
    for k in range(first, nframes):
        if k in set(reset_frames):
            state = np.full(K, 1 / K, dtype=f32)
            reset_t.append(k * hop / fs)
        if state is None:
            state = prob[k].astype(f32)
        else:
            state = (f32(alpha) * state + (f32(1) - f32(alpha)) * prob[k]).astype(f32)
        y[k] = state
    return y, reset_t
