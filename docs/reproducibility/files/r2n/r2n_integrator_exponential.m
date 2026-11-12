function [y, reset_t] = r2n_integrator_exponential(prob, alpha, reset_frames, first, hop, fs)
%R2N_INTEGRATOR_EXPONENTIAL  ros2neuro_integrator_exponential: state = alpha*state + (1-alpha)*prediction, in single.
%   prob : [frames K] decoder output (single, NaN before frame 'first'); alpha : smoothing (0..1);
%   reset_frames : frames at which the state goes back to 1/K (the integrator's reset event or the /reset service); first : first frame
%   with a prediction (default 1); hop, fs : samples per frame and sampling rate, only to return the time of every reset.
%   The first prediction of the run becomes the state; at a reset the state is all 1/K and the frame is integrated from there. ROS integrates the frame that contains the event and resets after it (the caller passes ceil(position/hop)+1).
if nargin < 3, reset_frames = []; end
if nargin < 4, first = 1; end
if nargin < 5, hop = 1; end
if nargin < 6, fs = 1; end
[nframes, K] = size(prob); y = nan(nframes, K, 'single'); state = []; reset_t = [];
for k = first:nframes
    if any(reset_frames == k)
        state = ones(1, K, 'single') / single(K); reset_t(end+1) = (k - 1) * hop / fs; %#ok<AGROW>
    end
    if isempty(state), state = prob(k, :); else, state = single(alpha) * state + (single(1) - single(alpha)) * prob(k, :); end
    y(k, :) = state;
end
end
