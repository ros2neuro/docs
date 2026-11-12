function check_evaluation(gdf_file, run_folder, launcher)
%CHECK_EVALUATION Redoes an EVALUATION of launch/gaussian_4class in MATLAB, from the recorded GDF, and compares it with ROS 2.
%
%   check_evaluation                                 newest GDF in ../recordings and newest CSV run in data/
%   check_evaluation(gdf_file)                       that GDF, newest CSV run
%   check_evaluation(gdf_file, run_folder)           that GDF and that CSV run
%   check_evaluation(gdf_file, run_folder, launcher) and the yaml and model of that launcher folder (with config/ and model/)
%
% With the example of the documentation (ros2neuro_matlab_example.zip unzipped here, folder example/) and no arguments it uses
% example/evaluation.gdf, example/run/ and example/gaussian_4class/: the reference run, no ROS 2 needed.
%
% Record both with:   ros2 launch ros2neuro_devel_test gaussian_4class_matlab.launch.xml     (about 2 minutes, then it ends by itself)
% (a GDF with the raw EEG and the events in ../recordings, a CSV of every topic in data/run_<date>/, see README.md).
%
% What it does, in the order of the chain:
%   1. loads the GDF (needs BIOSIG: sload) and the yaml of the launcher (launch/gaussian_4class/config and model);
%   2. FILTERS    Laplacian
%   3. DECODER    Welch PSD (ln) + Gaussian classifier
%   4. INTEGRATOR exponential, reset at every CFeedback (781); the outcome of every trial recomputed and compared with the one in the GDF
%   5. compares every stage with what ROS 2 published (the CSV), when there is a run;
%   6. FIGURES, ROS 2 vs MATLAB, with Start / Fixation / cue / CFeedback / Hit / Miss / Timeout marked in all of them:
%        1 filters (C3, C4: raw; filtered ROS 2 and MATLAB; their difference)   2 the features the model uses (/processing/psd)
%        3 classification (/classification/prediction)                          4 integration (/integrated/raw) and thresholds
% Every parameter comes from the yaml, nothing is typed here. Everything ROS 2 does in float32 is done in single.

here = fileparts(mfilename('fullpath'));
pkg = fileparts(here);
example = fullfile(here, 'example');
if isfolder(example)                                  % the example of the documentation
    def_gdf = fullfile(example, 'evaluation.gdf'); def_run = fullfile(example, 'run'); def_launcher = fullfile(example, 'gaussian_4class');
else                                                  % inside ros2neuro_devel_test
    def_gdf = ''; def_run = ''; def_launcher = fullfile(pkg, 'launch', 'gaussian_4class');
end
if nargin < 3 || isempty(launcher), launcher = def_launcher; end
conf = fullfile(launcher, 'config');
if nargin < 1 || isempty(gdf_file)
    if ~isempty(def_gdf), gdf_file = def_gdf; else, gdf_file = newest(fullfile(pkg, 'recordings', '*_evaluation_*.gdf')); end
end
if nargin < 2 || isempty(run_folder)
    if ~isempty(def_run), run_folder = def_run; else, run_folder = latest_run(fullfile(here, 'data')); end
end
out = fullfile(here, 'results');
if ~isfolder(out), mkdir(out); end
use_biosig();

addpath(fullfile(fileparts(mfilename('fullpath')), 'r2n'));   % the functions of every stage (see check_functions.m)

%% 1. the GDF and the yaml of the launcher ------------------------------------------------------------------------------------
[s, h] = sload(gdf_file);
fs = h.SampleRate;
eeg = single(s(:, 1:end-1));                                 % the last channel is the trigger
ev = struct('type', h.EVENT.TYP, 'pos', h.EVENT.POS, 'dur', h.EVENT.DUR);   % pos: sample (1-based), dur: samples (Off already merged)
fprintf('\nGDF %s\n  %d samples x %d channels, %g Hz, %d events\n', gdf_file, size(eeg, 1), size(eeg, 2), fs, numel(ev.type));

pipeline = fullfile(conf, 'pipeline.yaml');
nch = r2n_yaml_value(pipeline, 'filters.laplacian.nchannels');
laplacian_layout = r2n_yaml_value(pipeline, 'filters.laplacian.layout');
welch.fs = r2n_yaml_value(pipeline, 'welch.samplerate');
welch.length = r2n_yaml_value(pipeline, 'welch.wlength');
welch.overlap = r2n_yaml_value(pipeline, 'welch.overlap');
welch.buffer = r2n_yaml_value(pipeline, 'welch.buffer');
welch.window = r2n_yaml_value(pipeline, 'welch.wtype');
welch.freqs = eval(['[' strrep(r2n_yaml_value(pipeline, 'welch.frequencies'), ',', ' ') ']']); %#ok<EVLDIR>
hop = round(fs / r2n_yaml_value(pipeline, 'acquisition.framerate'));            % samples per frame: 32
classes = r2n_yaml_value(fullfile(conf, 'layout.yaml'), 'classes');
thresholds = r2n_yaml_value(fullfile(conf, 'layout.yaml'), 'thresholds');
alpha = single(r2n_yaml_value(fullfile(conf, 'integrator_exponential.yaml'), 'integrator.params.alpha'));
reset_event = r2n_yaml_value(fullfile(conf, 'integrator_exponential.yaml'), 'integrator.reset_event');
timeout_ms = r2n_yaml_value(fullfile(conf, 'protocol_evaluation.yaml'), 'duration.timeout');
model_dir = fullfile(launcher, 'model');
model = r2n_gaussian_read(fullfile(model_dir, r2n_yaml_value(fullfile(model_dir, 'manifest.yaml'), 'path')));
K = numel(classes);
names = containers.Map({769, 770, 771, 773, 783}, {'LEFT HAND', 'RIGHT HAND', 'BOTH FEET', 'BOTH HANDS', 'REST'});
fprintf('  classes %s, thresholds %s, alpha %g, integrator reset on event %d, %d samples per frame\n', mat2str(classes), mat2str(thresholds), alpha, reset_event, hop);


%% 2. filters: Laplacian ------------------------------------------------------------------------------------------------------
filt = r2n_laplacian(eeg, laplacian_layout);                 % float32, like Eigen

%% 3. decoder: Welch PSD + Gaussian -------------------------------------------------------------------------------------------
nframes = floor(size(eeg, 1) / hop);
need = welch.buffer / hop;                                   % frames in the buffer (16)
first = need;                                                % the first frame with a full 512-sample buffer
nfreq = numel(welch.freqs);
psd = nan(nframes, nch * nfreq, 'single');
prob = nan(nframes, K, 'single');
for k = first:nframes
    x = double(filt((k - need) * hop + 1:k * hop, :));
    p = single(r2n_welch(x, welch));                         % [freq channel], published as float32
    psd(k, :) = reshape(p, 1, []);                           % channel-major, like the feature
    prob(k, :) = r2n_gaussian_predict(model, psd(k, :));
end
tk = (1:nframes)' * hop / fs;                                % the time of the end of every frame

%% 4. integrator: exponential, reset at the start of every continuous feedback --------------------------------------------------
reset_pos = ev.pos(ev.type == reset_event);
% The rule: ROS 2 integrates the frame that contains the event (the one that ends after it) and resets after it, so the first frame
% integrated after the reset is the next one. It holds when the frame reaches the integrator before the event. The events and the values
% travel on different topics and their order is not guaranteed: now and then the event overtakes the frame and the reset is one frame
% earlier. MATLAB cannot know the order, so when there is a CSV run the resets are taken as ROS 2 made them (the reset messages of
% integrated.csv), and the rule is only compared with them (the line "resets" below).
rule_frame = ceil(reset_pos / hop) + 1;
reset_frame = rule_frame;
frame_of = align_csv(run_folder, eeg, hop, nch);
if ~isempty(frame_of)
    seen = observed_resets(run_folder, frame_of);
    if numel(seen) == numel(rule_frame) && max(abs(seen - rule_frame)) <= 1, reset_frame = seen; end
end
[integ, reset_t] = r2n_integrator_exponential(prob, alpha, reset_frame, first, hop, fs);

% the outcome of every trial, recomputed: the first class over its threshold during the continuous feedback decides
fprintf('\n  trial  cue   continuous feedback (s)   outcome in the GDF   recomputed from the integrator   \n');
cf = find(ev.type == 781);
agree = 0;
for i = 1:numel(cf)
    cue = ev.type(find(ismember(ev.type(1:cf(i)-1), classes), 1, 'last'));       % the cue before this CFeedback
    a = ceil(ev.pos(cf(i)) / hop) + 1; b = ceil((ev.pos(cf(i)) + ev.dur(cf(i))) / hop);   % from the first frame after the reset to the one of the outcome
    if reset_event == 781 && numel(reset_frame) == numel(cf), a = reset_frame(i); end          % the reset as it happened
    verdict = 'Timeout'; 
    for k = a:b
        w = r2n_threshold_winner(thresholds, integ(k, :));
        if w > 0
            verdict = 'Miss'; if classes(w) == cue, verdict = 'Hit'; end
            break
        end
    end
    if ev.dur(cf(i)) / fs * 1000 < timeout_ms && strcmp(verdict, 'Timeout'), verdict = 'Timeout?'; end
    gdf = ev.type(cf(i) + 1);                                                    % the outcome event follows the CFeedback
    gdf_name = {'897', 'Hit'; '898', 'Miss'; '899', 'Timeout'};
    gdf_text = gdf_name{strcmp(gdf_name(:, 1), num2str(gdf)), 2};
    same = strcmp(gdf_text, verdict); agree = agree + same;
    fprintf('  %3d   %d   %6.2f .. %6.2f           %-8s             %-8s  %s\n', i, cue, ev.pos(cf(i)) / fs, (ev.pos(cf(i)) + ev.dur(cf(i))) / fs, gdf_text, verdict, ifelse(same, 'same', '<-- different'));
end
fprintf('  %d of %d outcomes recomputed from the integrated values are the ones of ROS 2\n', agree, numel(cf));


%% 5. against ROS 2 ----------------------------------------------------------------------------------------------------------
% prints PASS / FAIL for every stage and returns what ROS 2 published on the frames of the GDF (NaN where there is nothing)
ros = compare_with_ros(run_folder, eeg, filt, psd, prob, integ, reset_frame, rule_frame, first, hop, nch, nfreq);

%% 6. figures: ROS 2 (blue, thick) vs MATLAB (red, dashed), with the events of the protocol -----------------------------------------
t_s = (1:size(eeg, 1))' / fs;                                % the time of every sample
known = find(~isnan(ros.filt(:, 1)));                        % the part of the run that ROS 2 recorded (the CSV)
xr = [t_s(1) t_s(end)]; if ~isempty(known), xr = t_s([known(1) known(end)])'; end
two = find(ismember(h.Label(1:nch), {'C3', 'C4'}));          % the motor cortex over the two hands: where the MI shows
if numel(two) < 2, two = 1:min(2, nch); end
BLUE = [0 0.35 0.85]; RED = [0.85 0.1 0.1];

fig1 = figure('Name', '1 filters', 'Position', [60 60 1500 850]);
for q = 1:numel(two)
    c = two(q); nm = h.Label{c};
    ax = subplot(3, 2, q); plot(t_s, eeg(:, c), 'Color', [0.35 0.35 0.35]); grid on; title([nm ': raw signal']); ylim(trial_range(eeg(:, c), t_s, xr));
    mark_events(ax, ev, fs, classes, names, q == 1);
    ax = subplot(3, 2, 2 + q); a = plot(t_s, ros.filt(:, c), 'Color', BLUE, 'LineWidth', 2.5); hold on; b = plot(t_s, filt(:, c), '--', 'Color', RED); grid on;
    title([nm ': after the Laplacian']); ylim(trial_range(filt(:, c), t_s, xr)); mark_events(ax, ev, fs, classes, names, false); legend([a b], 'ROS 2', 'MATLAB', 'Location', 'northeast');
    ax = subplot(3, 2, 4 + q); plot(t_s, ros.filt(:, c) - filt(:, c), 'k'); grid on; title([nm ': ROS 2 - MATLAB']); xlabel('s');
    mark_events(ax, ev, fs, classes, names, false);
end
finish(fig1, xr, fullfile(out, 'fig1_filters.png'));

sel = double(model.selection_channel) * nfreq + double(model.selection_frequency) + 1;   % the features the model uses
labels = arrayfun(@(i) sprintf('%s @ %g Hz', h.Label{model.selection_channel(i) + 1}, welch.freqs(model.selection_frequency(i) + 1)), 1:numel(sel), 'UniformOutput', false);
fig2 = figure('Name', '2 features', 'Position', [80 80 1500 850]);
for i = 1:numel(sel)
    ax = subplot(ceil(numel(sel) / 2), 2, i); a = plot(tk, ros.psd(:, sel(i)), 'Color', BLUE, 'LineWidth', 2.5); hold on; b = plot(tk, psd(:, sel(i)), '--', 'Color', RED); grid on;
    title([labels{i} ' (ln power)']); mark_events(ax, ev, fs, classes, names, i <= 2);
    if i == 1, legend([a b], 'ROS 2 (/processing/psd)', 'MATLAB', 'Location', 'southeast'); end
end
finish(fig2, xr, fullfile(out, 'fig2_features.png'));

fig3 = figure('Name', '3 classification', 'Position', [100 100 1500 850]);
for c = 1:K
    ax = subplot(K, 1, c); a = plot(tk, ros.prob(:, c), 'Color', BLUE, 'LineWidth', 2.5); hold on; b = plot(tk, prob(:, c), '--', 'Color', RED); grid on;
    ylim([0 1]); ylabel(sprintf('%d %s', classes(c), names(classes(c)))); mark_events(ax, ev, fs, classes, names, c == 1);
    if c == 1, title('Gaussian decoder: probability of every class (/classification/prediction)'); legend([a b], 'ROS 2', 'MATLAB', 'Location', 'northeast'); end
end
xlabel('s'); finish(fig3, xr, fullfile(out, 'fig3_classification.png'));

fig4 = figure('Name', '4 integration', 'Position', [120 120 1500 850]);
ax = subplot(3, 1, 1:2); hold on; colors = lines(K); a = gobjects(1, K);
for c = 1:K, yline(ax, thresholds(c), ':', sprintf('th %g', thresholds(c)), 'Color', colors(c, :), 'LabelHorizontalAlignment', 'left', 'HandleVisibility', 'off'); end
for c = 1:K, a(c) = plot(ax, tk, ros.integ(:, c), 'Color', colors(c, :), 'LineWidth', 2.5); end
b = plot(ax, tk, integ, 'k--'); plot(ax, reset_t, ones(size(reset_t)) / K, 'k.', 'MarkerSize', 12, 'HandleVisibility', 'off'); grid on; ylim([0 1]);
title(sprintf('integrator (exponential, alpha %g), reset to 1/K at every CFeedback (black dots): ROS 2 coloured, MATLAB black dashed', alpha)); ylabel('integrated value');
mark_events(ax, ev, fs, classes, names, true);
legend([a b(1)], [arrayfun(@(c) sprintf('%d %s (ROS 2)', c, names(c)), classes, 'UniformOutput', false) {'MATLAB'}], 'Location', 'eastoutside');
ax = subplot(3, 1, 3); semilogy(tk, ros.err + eps('single'), '.', 'Color', 'k'); grid on; xlabel('s');
title('|ROS 2 - MATLAB| (counted after the first reset: before it ROS 2 and MATLAB start from different histories)'); mark_events(ax, ev, fs, classes, names, false);
finish(fig4, xr, fullfile(out, 'fig4_integration.png'));

fprintf('\nFigures saved in %s\n', out);
end


%% ------------------------------------------------------------------------------------------------------------------------------
function ros = compare_with_ros(folder, eeg, filt, psd, prob, integ, reset_frame, rule_frame, first, hop, nch, nfreq) %#ok<INUSD>
%COMPARE_WITH_ROS Prints PASS / FAIL for every stage; returns what ROS 2 published, on the samples / frames of the GDF (NaN where there is none).
ros.filt = nan(size(eeg), 'single'); ros.psd = nan(size(psd), 'single'); ros.prob = nan(size(prob), 'single');
ros.integ = nan(size(integ), 'single'); ros.err = nan(size(psd, 1), 1);
if ~isfolder(folder)
    fprintf('\nNo CSV run in data/: record one with gaussian_4class_matlab.launch.xml to compare with ROS 2 (the figures show MATLAB only).\n');
    return
end
fprintf('\nROS 2 run %s\n', folder);
frame_of = align_csv(folder, eeg, hop, nch);
if isempty(frame_of)
    fprintf('  the GDF and the CSV run are not from the same session (the first raw sample of the CSV is not in the GDF): nothing to compare\n');
    return
end

filtered = read_table(fullfile(folder, 'filtered.csv'));
ros_f = permute(reshape(single(filtered.data(:, 6:5+nch))', nch, hop, []), [2 1 3]);
kf = frame_of(filtered.data(1:hop:end, 3:4));
e = 0;
for i = 1:numel(kf)
    idx = (kf(i)-1)*hop + (1:hop); ros.filt(idx, :) = ros_f(:, :, i);
    e = max(e, max(abs(ros_f(:, :, i) - filt(idx, :)), [], 'all'));
end
report('filters (Laplacian)', e, 1e-6 * max(abs(eeg), [], 'all'), 'max |ROS - MATLAB|, tolerance 1e-6 of the largest sample (float32)');

p = read_table(fullfile(folder, 'psd.csv'));
k = frame_of(p.data(:, 3:4)); ok = k >= first; ros.psd(k, :) = single(p.data(:, 5:end));
e = max(abs(ros.psd(k(ok), :) - psd(k(ok), :)), [], 'all');
report('Welch PSD (ln)', e, 1e-3, sprintf('%d windows, from the MATLAB filter output', sum(ok)));

d = read_table(fullfile(folder, 'prediction.csv'));
k = frame_of(d.data(:, 3:4)); ok = k >= first; ros.prob(k, :) = single(d.data(:, 6:end));
e = max(abs(ros.prob(k(ok), :) - prob(k(ok), :)), [], 'all');
report('Gaussian decoder', e, 1e-3, sprintf('%d predictions, from the MATLAB PSD', sum(ok)));

g = read_table(fullfile(folder, 'integrated.csv'));
dup = [false; all(diff(g.data(:, 3:4)) == 0, 2)];             % the reset messages repeat the stamp of the message before
keep = ~dup;
k = frame_of(g.data(keep, 3:4)); v = single(g.data(keep, 6:end)); ros.integ(k, :) = v;
after = k >= min(reset_frame) & k >= first;                    % once the first reset has happened the state depends on the events only
err = max(abs(v(after, :) - integ(k(after), :)), [], 2); ros.err(k(after)) = err;
report('integrator (after the first reset)', max(err), 1e-3, sprintf('%d frames, reset at every CFeedback, from the MATLAB decoder', sum(after)));
ros_resets = sum(dup);
if ros_resets ~= numel(rule_frame)
    report('resets', abs(ros_resets - numel(rule_frame)), 0, sprintf('%d in ROS 2, %d CFeedback in the GDF', ros_resets, numel(rule_frame)));
else
    shift = reset_frame(:) - rule_frame(:);                   % 0: where the rule puts it; -1: the event overtook the frame
    report('resets (frame vs the rule)', max(abs(shift)), 1, sprintf('%d resets: %d at the frame of the rule, %d one frame off (the event and the frame travel on different topics)', ros_resets, sum(shift == 0), sum(shift ~= 0)));
end
end

function frame_of = align_csv(folder, eeg, hop, nch)
%ALIGN_CSV Where the CSV run is inside the GDF. Returns frame_of(stamps): the frame of the GDF of each message of the CSV (by header stamp),
%   or [] when there is no run or it is not the session of the GDF.
frame_of = [];
if ~isfolder(folder), return, end
raw = read_table(fullfile(folder, 'raw.csv'));
r1 = single(raw.data(1, 6:5+nch));                            % the first raw sample of the CSV is somewhere in the GDF
at = find(all(abs(eeg - r1) <= 1e-3 * max(1, abs(r1)), 2), 1);
if isempty(at) || mod(at - 1, hop) ~= 0, return, end
off = (at - 1) / hop;                                         % frames of the GDF before the first frame of the CSV
stamp_of = raw.data(1:hop:end, 3:4);                          % header stamp of every raw frame of the CSV
frame_of = @(stamps) arrayfun(@(i) find(all(stamp_of == stamps(i, :), 2), 1), 1:size(stamps, 1))' + off;
end

function frames = observed_resets(folder, frame_of)
%OBSERVED_RESETS The frame at which ROS 2 reset the integrator, once per reset message of integrated.csv. A reset message repeats the stamp
%   of the message before it, so the frame before the reset is the frame of that one, and the first frame integrated after it is the next.
g = read_table(fullfile(folder, 'integrated.csv'));
dup = [false; all(diff(g.data(:, 3:4)) == 0, 2)];
frames = frame_of(g.data(find(dup) - 1, 3:4)) + 1;
end

function report(name, value, tol, note)
verdict = 'PASS'; if ~(value <= tol), verdict = 'FAIL'; end
fprintf('  %-36s %10.3g (tolerance %7.3g)  %s  %s\n', name, value, tol, verdict, note);
end

function mark_events(ax, ev, fs, classes, names, lab) %#ok<INUSD>
%MARK_EVENTS Start, Fixation, cue, continuous feedback (CF) and outcome (Hit / Miss / Timeout) of every trial, on the current time axis.
%   lab = false: only the marks, no text (for the axes below the first one of a figure).
hold(ax, 'on'); yl = ylim(ax); ylim(ax, yl); y1 = yl(2); dy = yl(2) - yl(1);
colors = lines(numel(classes));
style = {897, 'g^', 'Hit'; 898, 'rx', 'Miss'; 899, 'ms', 'Timeout'};
for i = 1:numel(ev.type)
    t = ev.type(i); a = ev.pos(i) / fs; b = (ev.pos(i) + ev.dur(i)) / fs;
    if t == 786                                              % Fixation
        band(ax, a, b, yl, [0.85 0.85 0.85], 0.45);
        if lab, text(ax, a, y1, 'Fixation', 'Rotation', 90, 'VerticalAlignment', 'top', 'HorizontalAlignment', 'right', 'FontSize', 7, 'Color', [0.4 0.4 0.4]); end
    elseif any(t == classes)                                 % the cue
        band(ax, a, b, yl, colors(t == classes, :), 0.25);
        if lab, text(ax, a, y1, sprintf('cue %d', t), 'Rotation', 90, 'VerticalAlignment', 'top', 'HorizontalAlignment', 'right', 'FontSize', 7, 'Color', colors(t == classes, :) * 0.7); end
    elseif t == 781                                          % continuous feedback
        band(ax, a, b, yl, [1 0.93 0.5], 0.4);
        xline(ax, a, 'k-', ifelse(lab, 'CF', ''), 'FontSize', 7, 'LabelVerticalAlignment', 'bottom', 'HandleVisibility', 'off');
    elseif any(t == [897 898 899])                           % Hit / Miss / Timeout
        row = find([style{:, 1}] == t);
        plot(ax, a, y1 - 0.04 * dy, style{row, 2}, 'MarkerSize', 9, 'LineWidth', 2, 'HandleVisibility', 'off');
        if lab, text(ax, a, y1 - 0.09 * dy, style{row, 3}, 'FontSize', 7, 'HorizontalAlignment', 'center'); end
    elseif t == 1
        xline(ax, a, ':', ifelse(lab, 'Start', ''), 'FontSize', 7, 'Color', [0.5 0.5 0.5], 'LabelVerticalAlignment', 'bottom', 'HandleVisibility', 'off');
    end
end
end

function band(ax, a, b, yl, color, alpha)
%BAND A shaded span of time, behind the curves.
p = patch(ax, [a b b a], [yl(1) yl(1) yl(2) yl(2)], color, 'EdgeColor', 'none', 'FaceAlpha', alpha, 'HandleVisibility', 'off');
uistack(p, 'bottom');
end

function yl = trial_range(x, t, xr)
%TRIAL_RANGE y limits for the signal of the trials: the first seconds of the file hold a large start-up transient that would flatten the rest
%   (the transient is still drawn, but clipped); they come from the second half of the time range.
x = double(x(t >= mean(xr) & t <= xr(2))); m = median(x); r = 4 * (prctile_sorted(x, 0.99) - prctile_sorted(x, 0.01));
yl = m + [-1 1] * max(r, eps);
end

function v = prctile_sorted(x, q)
x = sort(x); v = x(max(1, round(q * numel(x))));
end

function finish(fig, xr, file)
%FINISH The same time range on every axis of the figure, then save it.
set(findall(fig, 'Type', 'axes'), 'XLim', xr);
drawnow; exportgraphics(fig, file, 'Resolution', 110);
end

function out = ifelse(c, a, b)
if c, out = a; else, out = b; end
end

function f = newest(pattern)
d = dir(pattern);
if isempty(d), error('check_evaluation:nogdf', 'No file %s: record one with gaussian_4class_matlab.launch.xml (see README.md)', pattern); end
[~, i] = max([d.datenum]);
f = fullfile(d(i).folder, d(i).name);
end

function folder = latest_run(data)
latest = fullfile(data, 'latest.txt');
folder = '';
if isfile(latest), folder = fullfile(data, strtrim(fileread(latest))); end
end

function use_biosig()
%USE_BIOSIG sload comes from BIOSIG. If it is not on the path, look for it where it is usually installed and add ONLY the folders it needs
%   (not its "maybe-missing" folder: it holds copies of MATLAB functions that must not hide the real ones).
if exist('sload', 'file'), return, end
home = getenv('HOME');
for c = {getenv('BIOSIG_PATH'), '/usr/local/share/biosig/matlab', fullfile(home, 'Local', 'Matlab', 'biosig'), fullfile(home, 'biosig')}
    if ~isempty(c{1}) && isfile(fullfile(c{1}, 't200_FileAccess', 'sload.m'))
        addpath(fullfile(c{1}, 't200_FileAccess'), fullfile(c{1}, 't210_Events'), fullfile(c{1}, 't250_ArtifactPreProcessingQualityControl'));
        return
    end
end
error('check_evaluation:biosig', 'sload not found: install BIOSIG (https://biosig.sourceforge.net) and add it to the path, or set BIOSIG_PATH to its folder');
end

function t = read_table(file)
fid = fopen(file, 'r'); t.names = strsplit(fgetl(fid), ','); fclose(fid);
t.data = readmatrix(file, 'NumHeaderLines', 1, 'Delimiter', ',');
end
