function f = r2n_fbcsp(window, W)
%R2N_FBCSP  ros2neuro_processing_fbcsp (FbcspCore.h): the FBCSP feature of one analysis window, from bands that are ALREADY band-passed.
%   window : cell array, one [buffer channels] matrix per band (the last `buffer` samples of the signal of that band, i.e. the output of the
%   filter chain of the band: hp at lo then lp at hi, see r2n_butterworth); W : [bands components channels] CSP filters (r2n_fbcsp_weights).
%   Per band, in double: z = x * W(b,:,:)' (every component), v = population variance of z (mean removed), the feature of component k is
%   log(max(v_k / sum_j v_j, 1e-12)) (0 if the total is 0). Returns the feature as a row, band-major (index = band * components + component),
%   float32 like the published feature.
nb = numel(window); comps = size(W, 2); f = zeros(1, nb * comps);
for b = 1:nb
    x = double(window{b}); Wb = reshape(W(b, :, :), size(W, 2), size(W, 3));
    z = x * Wb'; v = mean((z - mean(z, 1)) .^ 2, 1); total = sum(v);
    if total > 0, frac = v / total; else, frac = zeros(1, comps); end
    f((b - 1) * comps + (1:comps)) = log(max(frac, 1e-12));
end
f = single(f);
end
