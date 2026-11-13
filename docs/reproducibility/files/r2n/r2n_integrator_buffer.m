function y = r2n_integrator_buffer(prob, buffer_size, increment, reset_frames, init_val)
%R2N_INTEGRATOR_BUFFER  ros2neuro_integrator_buffer (Buffer.cpp) in single.
%   prob : [frames K] decoder output; buffer_size : the steps to go from 0 to 1; increment : 0 hard (step 1/buffer_size) or
%   1 soft (step = winning value / buffer_size); reset_frames : frames at which the buffer goes back to its reset state before the
%   frame is integrated; init_val : the reset state (normalized to sum 1; default the uniform 1/K). The buffer starts from the reset state.
%   Per frame the class with the highest value (the first one on a tie) goes up by the step (at most to 1) and the same amount is
%   taken from the others in equal shares; a class that would go below 0 stops at 0 and the rest of its share goes to the others.
if nargin < 4, reset_frames = []; end
[nframes, K] = size(prob);
if nargin < 5 || isempty(init_val), start = ones(1, K, 'single') / single(K);
else, init_val = double(single(init_val)); start = single(init_val / sum(init_val)); end
prob = single(prob); y = zeros(nframes, K, 'single'); data = start;
for f = 1:nframes
    if any(reset_frames == f), data = start; end
    [~, w] = max(prob(f, :));
    if increment == 0, step = single(1) / single(buffer_size); else, step = prob(f, w) / single(buffer_size); end
    gain = min(step, single(1) - data(w)); data(w) = data(w) + gain; remaining = gain;
    while remaining > single(1e-9)
        active = find((1:K) ~= w & data > 0);
        if isempty(active), break; end
        share = remaining / single(numel(active));
        for i = active
            taken = min(data(i), share); data(i) = data(i) - taken; remaining = remaining - taken;
        end
    end
    y(f, :) = data;
end
end
