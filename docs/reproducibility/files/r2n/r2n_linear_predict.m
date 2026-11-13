function [p, score] = r2n_linear_predict(m, feature_row)
%R2N_LINEAR_PREDICT  ros2neuro_decoder_lda (LDA.cpp) and ros2neuro_decoder_svm (SVM.cpp) in single: the same arithmetic.
%   m : struct of r2n_linear_read; feature_row : the PSD feature, channel-major (all channels x all frequencies of the model).
%   score_k = bias_k + sum_i w_ki x_i (added in the order of the selection), then exp(score - max) / sum (TYPE_PROBABILITIES).
%   Returns the probabilities and the scores (what the node publishes for a model with TYPE_SCORES).
nfreq = numel(m.frequencies);
x = single(feature_row(:)); x = x(double(m.selection_channel) * nfreq + double(m.selection_frequency) + 1);
score = zeros(1, m.n_classes, 'single');
for k = 1:m.n_classes
    s = m.bias(k);
    for i = 1:numel(x), s = s + m.weights(k, i) * x(i); end
    score(k) = s;
end
p = r2n_softmax(score);
end
