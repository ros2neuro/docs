function p = r2n_gaussian_predict(m, psd_row)
%R2N_GAUSSIAN_PREDICT  ros2neuro_decoder_gaussian (Gaussian.cpp) in single: the probability of every class for one PSD feature.
%   m : struct of r2n_gaussian_read; psd_row : the feature, channel-major (all channels x all frequencies of the model), one row.
%   Per class the log-sum-exp over the prototypes of sum(-0.5 d^2/v - 0.5 ln v), plus ln(prior); exp(score - max), divided by the sum.
nfreq = numel(m.frequencies);
x = single(psd_row(:)); x = x(double(m.selection_channel) * nfreq + double(m.selection_frequency) + 1);
score = zeros(1, m.n_classes, 'single');
for k = 1:m.n_classes
    act = zeros(1, m.prototypes, 'single');
    for q = 1:m.prototypes
        d = x - m.centers(:, q, k); v = m.covariances(:, q, k); a = single(0);
        for j = 1:numel(x), a = a + (single(-0.5) * ((d(j) * d(j)) / v(j)) - single(0.5) * log(v(j))); end
        act(q) = a;
    end
    mx = max(act); s = mx + log(sum(exp(act - mx), 'native'));
    if ~isempty(m.priors) && m.priors(k) > 0, s = s + log(m.priors(k)); end
    score(k) = s;
end
raw = exp(score - max(score)); p = raw / sum(raw, 'native');
end
