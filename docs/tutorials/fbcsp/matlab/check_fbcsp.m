function ok = check_fbcsp(gdf_file, fbcsp_yaml, lda_yaml, features_file, prediction_file)
%CHECK_FBCSP  Does the ros2neuro fbcsp node give what MATLAB gives? And the LDA decoder?
%
%   check_fbcsp(gdf_file, 'config/fbcsp.yaml', 'config/fbcsp_lda.yaml', 'features.csv', 'prediction.csv')
%
%   gdf_file         the recording that was replayed
%   fbcsp_yaml       the parameters of the node (written by train_fbcsp.m)
%   lda_yaml         the LDA (written by train_fbcsp.m)
%   features_file    what the node published:  ros2 topic echo /processing/fbcsp --field data --csv > features.csv
%   prediction_file  what the decoder published: ros2 topic echo /classification/prediction --field values --csv > prediction.csv
%
%   MATLAB filters the whole recording with the coefficients of the yaml (filter(), double), applies W and takes ln of the mean square of
%   the last `window` samples every 32 samples. The messages are saved some seconds after the replay starts: the check looks for the window
%   its first message belongs to, then compares every message with its window. Needs r2n/ (r2n_yaml_value) and BIOSIG (sload).
assert(exist('r2n_yaml_value', 'file') == 2, 'add the r2n/ folder of ros2neuro_matlab to the path');
[s, h] = sload(gdf_file); nch = 16; eeg = double(s(:, 1:nch)); hop = 32; %#ok<NASGU>
win = r2n_yaml_value(fbcsp_yaml, 'window'); ncomp = r2n_yaml_value(fbcsp_yaml, 'components'); nb = r2n_yaml_value(fbcsp_yaml, 'n_bands');

%% what MATLAB computes ---------------------------------------------------------------------------------------------------------------
t_end = win:hop:size(eeg, 1); M = zeros(numel(t_end), ncomp * nb);
for b = 1:nb
    k = @(name) r2n_yaml_value(fbcsp_yaml, sprintf('band_%d.%s', b, name));
    x = filter(k('lp_b'), k('lp_a'), filter(k('hp_b'), k('hp_a'), eeg));
    W = reshape(k('w'), ncomp, nch)';                               % written row-major [channels x components]
    c = x * W; q = c .^ 2; cs = [zeros(1, ncomp); cumsum(q, 1)];
    for j = 1:numel(t_end)
        M(j, (0:ncomp-1) * nb + b) = log(max((cs(t_end(j) + 1, :) - cs(t_end(j) - win + 1, :)) / win, 1e-12));
    end
end

%% the node: every message against its window -----------------------------------------------------------------------------------------
R = read_array_lines(features_file);
limit = size(M, 1);                                                  % the first pass of the file (the node does not restart its filters when it loops)
[off, err] = best_offset(R, M);
n = min(size(R, 1), limit - off);
d = abs(R(1:n, :) - M(off + (1:n), :));
tol = 4 * double(eps(single(max(abs(R(:))))));                       % 4 ULP of float32 at the largest feature
results = {sprintf('fbcsp features (%d messages, the first one is the window %d of the file)', n, off + 1), max(d(:)), tol};

%% the decoder: softmax of the LDA on the features the node published -----------------------------------------------------------------
P = read_array_lines(prediction_file);
txt = fileread(lda_yaml);
rows = regexp(txt, '^\s*-\s*\[([^\]]*)\]', 'tokens', 'lineanchors');
Wl = cell2mat(cellfun(@(r) sscanf(strrep(r{1}, ',', ' '), '%f')', rows(:), 'uni', 0));
bias = r2n_yaml_value(lda_yaml, 'bias');
Z = R * Wl' + bias; E = exp(Z - max(Z, [], 2)); Pm = E ./ sum(E, 2);
[offp, ~] = best_offset(P, Pm);
np = min(size(P, 1), size(Pm, 1) - offp);
dp = abs(P(1:np, :) - Pm(offp + (1:np), :));
% The decoder adds the scores in float32: their size (here ~130) sets the rounding, 1 ULP = eps(single(130)) = 1.5e-5, and a probability
% moves by at most 0.25 for a unit of score. So 4 ULP of the largest score x 0.25 is the most float32 can explain.
tolp = 0.25 * 4 * double(eps(single(max(abs(Z(:))))));
results(2, :) = {sprintf('LDA decoder (%d messages)', np), max(dp(:)), tolp};

%% report -----------------------------------------------------------------------------------------------------------------------------
ok = true; fprintf('\n');
for i = 1:size(results, 1)
    pass = results{i, 2} <= results{i, 3}; ok = ok && pass;
    fprintf('  %-4s %-60s max |ROS - MATLAB| %.3g (tolerance %.3g)\n', ifelse(pass, 'PASS', 'FAIL'), results{i, 1}, results{i, 2}, results{i, 3});
end
fprintf('  mean difference of the features %.3g, first match at error %.3g\n\n', mean(d(:)), err);
if ~ok, error('check_fbcsp:failed', 'the node and MATLAB differ'); end
end

%% ---------------------------------------------------------------------------------------------------------------------------------
function A = read_array_lines(file)
% `ros2 topic echo --csv` of a float array prints  array('f', [1.0, 2.0, ...])  one line per message
lines = regexp(fileread(file), '\r?\n', 'split'); lines = lines(contains(lines, '['));      % one line per message ('---' separates them)
A = nan(numel(lines), 0);
for i = 1:numel(lines)
    v = sscanf(strrep(regexprep(regexprep(lines{i}, '^[^\[]*\[', ''), '\].*$', ''), ',', ' '), '%f')';
    A(i, 1:numel(v)) = v; %#ok<AGROW>
end
end

function [off, err] = best_offset(R, M)
% how many frames the messages of R are behind the windows of M. The recording starts when the acquisition is launched and the messages are
% saved later, so the first message is some frames in. Message r0 (taken a bit after the start, so that a late start of the node does not
% matter) is compared with every window from r0 on, and the one with the smallest difference wins.
r0 = min(100, size(R, 1)); e = inf(1, size(M, 1));
for j = r0:size(M, 1), e(j) = max(abs(R(r0, :) - M(j, :))); end
[err, j] = min(e); off = j - r0;
end

function r = ifelse(c, a, b), if c, r = a; else, r = b; end, end
