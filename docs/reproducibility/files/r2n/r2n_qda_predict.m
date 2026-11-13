function [p, score] = r2n_qda_predict(m, feature_row)
%R2N_QDA_PREDICT  ros2neuro_decoder_qda (QDA.cpp) in single.
%   m : struct of r2n_qda_read; feature_row : the PSD feature, channel-major (all channels x all frequencies of the model).
%   score_k = bias_k + sum_i l_ki x_i + sum_row sum_col x_row q_k(row, col) x_col (added in this order), then
%   exp(score - max) / sum. Returns the probabilities and the scores.
nfreq = numel(m.frequencies);
x = single(feature_row(:)); x = x(double(m.selection_channel) * nfreq + double(m.selection_frequency) + 1);
S = numel(x); score = zeros(1, m.n_classes, 'single');
for k = 1:m.n_classes
    s = m.bias(k);
    for i = 1:S, s = s + m.linear(k, i) * x(i); end
    for r = 1:S
        for c = 1:S, s = s + x(r) * m.quadratic(r, c, k) * x(c); end
    end
    score(k) = s;
end
p = r2n_softmax(score);
end
