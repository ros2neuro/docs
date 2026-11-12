function train_fbcsp(gdf_file, out_dir)
%TRAIN_FBCSP  Trains a filter bank CSP and an LDA on a recording of motor imagery, and writes what ros2neuro needs.
%
%   train_fbcsp('test_mi.gdf', 'out')
%
%   Reads a GDF with the events of the protocol (cue 771 / 773, then CFeedback 781 for the part where the subject imagines)
%   and writes in out_dir:
%       fbcsp.yaml       parameters of the fbcsp_node: channels, window, and for every band the filters and the spatial filters W
%       fbcsp_lda.yaml   the trained LDA, for write_fbcsp_lda (it makes the .r2nd and the manifest of the decoder)
%
%   It needs the ros2neuro MATLAB functions on the path (addpath('.../ros2neuro_matlab/r2n'), from the page "Reproducibility in
%   MATLAB") and BIOSIG for sload. No toolbox. This is an EXAMPLE of the method, not a tuned classifier: change the bands, the number of
%   components and the epoch to your data.
%
%   The online node does, sample by sample, what is done here with filter(): the same band-pass (a high-pass and a low-pass of order 2,
%   as r2n_butterworth designs them), W, and ln of the mean square of the last `win` samples every `hop` samples.

%% settings ------------------------------------------------------------------------------------------------------------------------
bands  = [8 12; 12 16; 16 20; 20 26];     % Hz: the filter bank
order  = 2;                               % of each of the two Butterworth sections of a band
m      = 1;                               % pairs of CSP filters per band: 2*m components per band
win    = 512;                             % samples the variance is computed on (1 s at 512 Hz)
hop    = 32;                              % samples between two features (the frame of the acquisition)
lambda = 0.1;                             % shrinkage of the covariance of the LDA
classes = [771 773];                      % event codes of the two classes (BOTH_FEET, BOTH_HANDS)
if nargin < 2, out_dir = 'fbcsp_out'; end
assert(exist('r2n_butterworth', 'file') == 2, 'add the r2n/ folder of ros2neuro_matlab to the path');
assert(exist('sload', 'file') == 2, 'sload (BIOSIG) is not on the path');

%% data ----------------------------------------------------------------------------------------------------------------------------
[s, h] = sload(gdf_file);
fs = h.SampleRate;
nch = 16;                                                       % the EEG channels of test_mi.gdf (the others are not EEG)
eeg = double(s(:, 1:nch));
labels = strtrim(cellstr(h.Label(1:nch, :)))';
typ = h.EVENT.TYP(:)'; pos = h.EVENT.POS(:)'; dur = h.EVENT.DUR(:)';
cf = find(typ == 781);                                          % the continuous feedback of every trial
ntr = numel(cf); y = zeros(1, ntr); first = zeros(1, ntr); last = zeros(1, ntr);
for i = 1:ntr
    cue = typ(find(ismember(typ(1:cf(i)-1), classes), 1, 'last'));
    y(i) = find(classes == cue);
    first(i) = pos(cf(i)); last(i) = pos(cf(i)) + dur(cf(i)) - 1;
end
fprintf('%s: %d trials (%d of class %d, %d of class %d), %d channels at %g Hz\n', gdf_file, ntr, sum(y == 1), classes(1), sum(y == 2), classes(2), nch, fs);

%% the filter bank: a causal band-pass of the whole recording, as the node does it ---------------------------------------------------
nb = size(bands, 1); xb = cell(1, nb); coef = cell(1, nb);
for b = 1:nb
    [~, bh, ah] = r2n_butterworth(zeros(8, 1), 'high', order, bands(b, 1), fs);
    [~, bl, al] = r2n_butterworth(zeros(8, 1), 'low',  order, bands(b, 2), fs);
    coef{b} = {bh, ah, bl, al};
    xb{b} = filter(bl, al, filter(bh, ah, eeg));                % double, like the node
end

%% leave-one-trial-out: the CSP is trained again in every fold, or the accuracy would be optimistic ------------------------------------
correct = 0; total = 0; trial_correct = 0;
for k = 1:ntr
    train = setdiff(1:ntr, k);
    model = fit(xb, first, last, y, train, m, win, hop, lambda);
    [F, ~] = features(xb, model.W, first(k), last(k), win, hop);
    pred = predict(model, F);
    correct = correct + sum(pred == y(k)); total = total + numel(pred);
    trial_correct = trial_correct + (mode(pred) == y(k));
end
fprintf('leave-one-trial-out: %.1f %% of the windows, %.1f %% of the trials (chance 50 %%, %d trials: read it as an indication)\n', ...
    100 * correct / total, 100 * trial_correct / ntr, ntr);

%% the final model, on every trial ---------------------------------------------------------------------------------------------------
model = fit(xb, first, last, y, 1:ntr, m, win, hop, lambda);
ncomp = 2 * m;
if ~exist(out_dir, 'dir'), mkdir(out_dir); end

% fbcsp.yaml: the parameters of fbcsp_node
fid = fopen(fullfile(out_dir, 'fbcsp.yaml'), 'w');
fprintf(fid, '# written by train_fbcsp.m from %s\nfbcsp:\n  ros__parameters:\n', gdf_file);
fprintf(fid, '    channels: [%s]\n', strjoin(cellfun(@(c) ['"' c '"'], labels, 'uni', 0), ', '));
fprintf(fid, '    window: %d\n    components: %d\n    n_bands: %d\n', win, ncomp, nb);
for b = 1:nb
    fprintf(fid, '    band_%d.centre: %s\n', b, num(mean(bands(b, :))));
    fprintf(fid, '    band_%d.hp_b: %s\n    band_%d.hp_a: %s\n', b, vec(coef{b}{1}), b, vec(coef{b}{2}));
    fprintf(fid, '    band_%d.lp_b: %s\n    band_%d.lp_a: %s\n', b, vec(coef{b}{3}), b, vec(coef{b}{4}));
    fprintf(fid, '    band_%d.w: %s\n', b, vec(reshape(model.W{b}.', 1, [])));    % row-major [channels x components]
end
fclose(fid);

% fbcsp_lda.yaml: the LDA, features in the order of the NeuroFeature: component-major, [component, band]
fid = fopen(fullfile(out_dir, 'fbcsp_lda.yaml'), 'w');
fprintf(fid, '# written by train_fbcsp.m\nname: fbcsp_lda\nsubject: tutorial\nsource: "train_fbcsp.m on %s"\nshrinkage: %g\n', ...
    strrep(gdf_file, '\', '/'), lambda);
fprintf(fid, 'classes: [%s]\n', strjoin(arrayfun(@(c) ['"' num2str(c) '"'], classes, 'uni', 0), ', '));
fprintf(fid, 'component_labels: [%s]\n', strjoin(arrayfun(@(k) sprintf('"csp%d"', k), 1:ncomp, 'uni', 0), ', '));
fprintf(fid, 'band_centres: %s\n', vec(mean(bands, 2)'));
fprintf(fid, 'weights:\n');
for c = 1:2, fprintf(fid, '  - %s\n', vec(model.weights(c, :))); end
fprintf(fid, 'bias: %s\n', vec(model.bias));
fclose(fid);
fprintf('written %s and %s\n', fullfile(out_dir, 'fbcsp.yaml'), fullfile(out_dir, 'fbcsp_lda.yaml'));
end

%% ---------------------------------------------------------------------------------------------------------------------------------
function model = fit(xb, first, last, y, train, m, win, hop, lambda)
% CSP of every band on the trials in `train`, then an LDA on the features of the windows of those trials
nb = numel(xb); model.W = cell(1, nb);
for b = 1:nb
    C = zeros(size(xb{b}, 2), size(xb{b}, 2), 2); n = [0 0];
    for i = train
        X = xb{b}(first(i):last(i), :); C(:, :, y(i)) = C(:, :, y(i)) + X' * X / trace(X' * X); n(y(i)) = n(y(i)) + 1;
    end
    C1 = C(:, :, 1) / n(1); C2 = C(:, :, 2) / n(2);
    [V, D] = eig(C1, C1 + C2); [~, o] = sort(diag(D));         % generalized eigenvalues: 0 = all the variance is of class 2, 1 = of class 1
    V = V(:, o); model.W{b} = V(:, [1:m, end-m+1:end]);         % the m filters at each end
end
F = []; L = [];
for i = train
    f = features(xb, model.W, first(i), last(i), win, hop); F = [F; f]; L = [L; y(i) * ones(size(f, 1), 1)]; %#ok<AGROW>
end
mu = [mean(F(L == 1, :), 1); mean(F(L == 2, :), 1)];
S = cov([F(L == 1, :) - mu(1, :); F(L == 2, :) - mu(2, :)]);   % pooled covariance
p = size(S, 1); S = (1 - lambda) * S + lambda * trace(S) / p * eye(p);
model.weights = (S \ mu')';                                      % one row per class
model.bias = -0.5 * sum(model.weights .* mu, 2)' + log([0.5 0.5]);
end

function [F, t_end] = features(xb, W, a, b, win, hop)
% ln of the mean square of every CSP component of every band, on the windows of `win` samples that end inside [a, b] every `hop` samples.
% One row per window; the columns are component-major, [component, band]: column = (component - 1) * bands + band.
nb = numel(xb); ncomp = size(W{1}, 2); t_end = (a + win - 1):hop:b;
F = zeros(numel(t_end), ncomp * nb);
for bd = 1:nb
    c = xb{bd}(a:b, :) * W{bd};                                  % the components over the trial
    for j = 1:numel(t_end)
        seg = c(t_end(j) - win + 1 - a + 1:t_end(j) - a + 1, :);
        F(j, (0:ncomp-1) * nb + bd) = log(max(mean(seg .^ 2, 1), 1e-12));
    end
end
end

function p = predict(model, F)
[~, p] = max(F * model.weights' + model.bias, [], 2);
p = p';
end

function t = num(v)
% a number as the yaml wants it: a decimal point, so that ROS reads a double and not an integer
t = sprintf('%.17g', v);
if isempty(regexp(t, '[.eEn]', 'once')), t = [t '.0']; end
end

function t = vec(v)
t = ['[' strjoin(arrayfun(@num, v(:)', 'uni', 0), ', ') ']'];
end
