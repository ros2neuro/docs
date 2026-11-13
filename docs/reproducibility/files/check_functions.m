function ok = check_functions(data_root)
%CHECK_FUNCTIONS  Checks every function of r2n/ (the MATLAB version of one ros2neuro stage) and prints PASS / FAIL for each.
%
%   check_functions                % ROS 2 data of reference/ when it is there (the downloaded zip), else of the packages in the
%                                  % workspace (../..), and the analytic checks
%   check_functions('/path/src')   % folder that holds the ros2neuro_filters_* packages
%   ok = check_functions;          % true when nothing failed (it also errors, so `matlab -batch check_functions` exits with 1)
%
%   Part 1, against ROS 2: the filters. The input and the output of the real node are the CSV that every filter package keeps in its
%   test/ folder (rawdata.csv and output_data*.csv, made by run_ros_pipeline.sh). The function must give what ROS 2 gave, to
%   a few ULP of float32: the tolerance is written in ULP of the largest INPUT sample (1 ULP = eps(single(max|raw|)), about 1e-3 for the
%   1e4 of rawdata.csv), not as a fixed number. The input sets the scale of the rounding because the filters add values of that size
%   (the mean of dc and car, the products of the Laplacian) even when what they output is much smaller (dc: 400).
%   If a package has no CSV the line says SKIPPED and how to make it: nothing is passed by default.
%   The zip of the documentation carries reference/: the first 512 samples of those CSV (every filter is causal or works one frame at a
%   time, so the first samples of the ROS 2 output are the filter of the first samples of the input) and the .r2nd of a test model.
%
%   Part 3, against ROS 2: the decoders LDA / QDA / SVM, the buffer integrator, the FFT and the spectrogram, on the inputs of stages/
%   and what the real node published for them (scripts/make_matlab_stages.py of ros2neuro_devel_test).
%
%   Part 2, analytic: functions that ROS 2 does not publish on their own (Welch, Gaussian, integrator, threshold, .r2nd reader) are checked
%   on cases whose answer is known by hand. Their comparison with ROS 2 is check_evaluation.m (whole chain, GDF + CSV of every topic).
here = fileparts(mfilename('fullpath'));
addpath(fullfile(here, 'r2n'));
reference = fullfile(here, 'reference');
if nargin < 1
    if isfolder(reference), data_root = reference; else, data_root = fullfile(here, '..', '..'); end
end
results = {};                                        % {status, name, text}

%% Part 1: filters vs ROS 2 --------------------------------------------------------------------------------------------------------
fs = 512; blk = 32; lap = [1 2 3; 4 5 6; 7 8 9];
F = {
    'r2n_car',                    'car',         'output_data.csv',          @(x) r2n_car(x),                          4
    'r2n_dc (32 samples/frame)',  'dc',          'output_data.csv',          @(x) r2n_dc(x, blk),                      8
    'r2n_laplacian (3x3 grid)',   'laplacian',   'output_data.csv',          @(x) r2n_laplacian(x, lap),               4
    'r2n_window hann',            'hann',        'output_data.csv',          @(x) r2n_window(x, 'hann', blk),          4
    'r2n_window hamming',         'hamming',     'output_data.csv',          @(x) r2n_window(x, 'hamming', blk),       4
    'r2n_window blackman',        'blackman',    'output_data.csv',          @(x) r2n_window(x, 'blackman', blk),      4
    'r2n_window flattop',         'flattop',     'output_data.csv',          @(x) r2n_window(x, 'flattop', blk),       4
    'r2n_butterworth low 40 Hz',  'butterworth', 'output_data_lowpass.csv',  @(x) r2n_butterworth(x, 'low', 4, 40, fs), 4
    'r2n_butterworth high 1 Hz',  'butterworth', 'output_data_highpass.csv', @(x) r2n_butterworth(x, 'high', 4, 1, fs), 4
    };
for i = 1:size(F, 1)
    results(end+1, :) = compare_one(data_root, F{i, 1}, ['ros2neuro_filters_' F{i, 2}], F{i, 3}, F{i, 4}, F{i, 5}); %#ok<AGROW>
end
chain = @(x) r2n_window(r2n_car(r2n_butterworth(r2n_butterworth(r2n_dc(x, blk), 'high', 4, 1, fs), 'low', 4, 40, fs)), 'hann', blk);
results(end+1, :) = compare_one(data_root, 'filter chain dc>hp 1>lp 40>car>hann', 'ros2neuro_filters', 'output_data.csv', chain, 8);

%% Part 2: analytic checks ---------------------------------------------------------------------------------------------------------
results(end+1, :) = analytic('r2n_car: every row sums to 0', @() max(abs(sum(double(r2n_car(randn(200, 8) * 1e3)), 2))) < 1e-2);
results(end+1, :) = analytic('r2n_dc: every block has mean 0', @() max(abs(mean(reshape(double(r2n_dc(randn(320, 4) * 1e3 + 5e3, 32)), 32, [], 4), 1)), [], 'all') < 1e-2);
results(end+1, :) = analytic('r2n_laplacian: a constant signal gives 0 (weights sum to 0)', @() max(abs(double(r2n_laplacian(ones(50, 9) * 7, [1 2 3; 4 5 6; 7 8 9]))), [], 'all') < 1e-5);
results(end+1, :) = analytic('r2n_window: hann/hamming/blackman/flattop are symmetric, hann is 0 at the ends', @() window_ok());
results(end+1, :) = analytic('r2n_butterworth: low-pass has gain 1 at DC, 0.707 at fc; high-pass the opposite', @() butter_ok(fs));
results(end+1, :) = analytic('r2n_welch: a 10 Hz sine of 1 uV peaks at 10 Hz', @() welch_ok());
results(end+1, :) = analytic('r2n_integrator_exponential: constant input stays; step follows alpha^n; reset gives 1/K', @() integrator_ok());
results(end+1, :) = analytic('r2n_gaussian_predict: probabilities sum to 1 and the nearest class wins', @() gaussian_ok());
results(end+1, :) = analytic('r2n_threshold_winner: none / one / the highest of two', @() threshold_ok());
results(end+1, :) = analytic('r2n_yaml_value: number, list, bool, text', @() yaml_ok());
f = [dir(fullfile(reference, '**', '*.r2nd')); dir(fullfile(here, '..', 'launch', '**', '*.r2nd'))];
if isempty(f)
    results(end+1, :) = {'SKIPPED', 'r2n_gaussian_read: reads a real .r2nd', 'no .r2nd found in reference/ or ../launch/'};
else
    results(end+1, :) = analytic(['r2n_gaussian_read: reads ' f(1).name], @() gaussian_read_ok(fullfile(f(1).folder, f(1).name)));
end

%% Part 3: the stages that check_evaluation does not run, against ROS 2 ------------------------------------------------------------
% stages/ (scripts/make_matlab_stages.py): fixed inputs and what the real nodes published for them: LDA, QDA, SVM (decoder_node,
% made-up models in stages/models/), buffer integrator hard and soft (integrator_node, buffer_size 10), fft_node (256 samples, hann,
% amplitude) and spectrogram_node (128 / overlap 64 over 512 samples, hamming, dB). The tolerance is in ULP of the largest ROS 2 value.
results = [results; stage_checks(fullfile(here, 'stages'))];

%% report ----------------------------------------------------------------------------------------------------------------------------
fprintf('\n');
for i = 1:size(results, 1), fprintf('  %-8s %-62s %s\n', results{i, 1}, results{i, 2}, results{i, 3}); end
nfail = sum(strcmp(results(:, 1), 'FAIL')); nskip = sum(strcmp(results(:, 1), 'SKIPPED'));
fprintf('\n  %d checks: %d PASS, %d FAIL, %d SKIPPED\n\n', size(results, 1), size(results, 1) - nfail - nskip, nfail, nskip);
ok = nfail == 0;
if ~ok, error('check_functions:failed', '%d check(s) failed', nfail); end
end

%% ---------------------------------------------------------------------------------------------------------------------------------
function row = compare_one(root, name, pkg, outfile, fn, ulps)
folder = fullfile(root, pkg, 'test');
raw_f = fullfile(folder, 'rawdata.csv'); out_f = fullfile(folder, outfile);
if ~isfile(raw_f) || ~isfile(out_f)
    row = {'SKIPPED', name, sprintf('no %s in %s (run its run_ros_pipeline.sh)', outfile, folder)}; return
end
raw = double(single(readmatrix(raw_f)));                 % csv_publisher.py sends every sample as float32
ros = readmatrix(out_f);
n = min(size(raw, 1), size(ros, 1));
y = double(fn(raw(1:n, :)));                              % the dc / window functions drop a last incomplete frame
n = min(n, size(y, 1));
d = abs(ros(1:n, :) - y(1:n, :)); [m, i] = max(d(:));
tol = ulps * double(eps(single(max(abs(raw(:))))));
status = 'PASS'; if ~(m <= tol), status = 'FAIL'; end
[s, c] = ind2sub(size(d), i);
row = {status, name, sprintf('max error %-9.3g (tolerance %.3g = %d ULP of the input %.4g)  worst at sample %d channel %d, %d values', m, tol, ulps, max(abs(raw(:))), s, c, numel(d))};
end

function row = analytic(name, fn)
try, good = fn(); catch err, row = {'FAIL', name, err.message}; return, end
row = {ifelse(good, 'PASS', 'FAIL'), name, ''};
end

function r = ifelse(c, a, b), if c, r = a; else, r = b; end, end

function g = window_ok()
g = true;
for n = {'hann', 'hamming', 'blackman', 'flattop'}
    [~, w] = r2n_window(ones(32, 1), n{1}, 32); g = g && max(abs(w - flipud(w))) < 1e-6;
end
[~, w] = r2n_window(ones(32, 1), 'hann', 32); g = g && abs(w(1)) < 1e-7 && abs(w(end)) < 1e-7;
end

function g = butter_ok(fs)
[~, bl, al] = r2n_butterworth(zeros(8, 1), 'low', 4, 40, fs);  [~, bh, ah] = r2n_butterworth(zeros(8, 1), 'high', 4, 40, fs);
h = @(b, a, f) abs(polyval(fliplr(b), exp(-1i * 2 * pi * f / fs)) / polyval(fliplr(a), exp(-1i * 2 * pi * f / fs)));
g = abs(h(bl, al, 0) - 1) < 1e-9 && abs(h(bl, al, 40) - sqrt(0.5)) < 1e-6 && abs(h(bh, ah, fs/2) - 1) < 1e-9 && abs(h(bh, ah, 40) - sqrt(0.5)) < 1e-6;
% when the Signal Processing Toolbox is there, the design is the one of butter()
if exist('butter', 'file') == 2
    [b2, a2] = butter(4, 40 / (fs / 2), 'low'); g = g && max(abs(bl - b2)) < 1e-12 && max(abs(al - a2)) < 1e-12;
    [b2, a2] = butter(4, 40 / (fs / 2), 'high'); g = g && max(abs(bh - b2)) < 1e-12 && max(abs(ah - a2)) < 1e-12;
end
end

function g = welch_ok()
w = struct('fs', 512, 'length', 256, 'overlap', 128, 'window', 'hann', 'freqs', 0:2:40);
t = (0:511)' / 512; x = sin(2 * pi * 10 * t);
p = r2n_welch(x, w); [~, i] = max(p); g = w.freqs(i) == 10;
end

function g = integrator_ok()
K = 2; n = 10; alpha = 0.9;
y = r2n_integrator_exponential(repmat(single([0.5 0.5]), n, 1), alpha);
g = max(abs(y(:) - 0.5)) < 1e-6;
p = [repmat(single([0.2 0.8]), 1, 1); repmat(single([0.9 0.1]), n, 1)];
y = r2n_integrator_exponential(p, alpha);          % first prediction is the state, then the step to 0.9
want = 0.9 - (0.9 - 0.2) * alpha ^ (n);
g = g && abs(y(end, 1) - want) < 1e-5;
y = r2n_integrator_exponential(p, alpha, 4);       % reset at frame 4: state 1/K, then integrates frame 4
g = g && abs(y(4, 1) - (alpha * 0.5 + (1 - alpha) * 0.9)) < 1e-6 && K == 2;
end

function g = gaussian_ok()
m.priors = [0.5 0.5]; m.frequencies = [10 20]; m.selection_channel = [0; 0]; m.selection_frequency = [0; 1];
m.prototypes = 1; m.n_classes = 2;
m.centers = cat(3, single([0; 0]), single([5; 5])); m.covariances = cat(3, single([1; 1]), single([1; 1]));
a = r2n_gaussian_predict(m, [0.1 -0.1]); b = r2n_gaussian_predict(m, [4.9 5.2]);
g = abs(sum(a) - 1) < 1e-6 && a(1) > 0.99 && b(2) > 0.99;
end

function g = threshold_ok()
g = r2n_threshold_winner([0.7 0.7], single([0.5 0.5])) == 0 && r2n_threshold_winner([0.7 0.7], single([0.3 0.7])) == 2 ...
    && r2n_threshold_winner([0.6 0.6], single([0.9 0.95])) == 2;
end

function g = yaml_ok()
f = [tempname '.yaml']; fid = fopen(f, 'w');
fprintf(fid, '# comment\nnum: 4.5   # trailing\nlst: [1, 2, 3]\nflag: true\ntxt: "hello"\n'); fclose(fid);
g = r2n_yaml_value(f, 'num') == 4.5 && isequal(r2n_yaml_value(f, 'lst'), [1 2 3]) && r2n_yaml_value(f, 'flag') && strcmp(r2n_yaml_value(f, 'txt'), 'hello');
delete(f);
end

function g = gaussian_read_ok(file)
m = r2n_gaussian_read(file);
g = m.n_classes >= 2 && numel(m.priors) == m.n_classes && abs(sum(m.priors) - 1) < 1e-4 && all(m.covariances(:) > 0) && numel(m.selection_channel) >= 1;
end

function rows = stage_checks(stages)
rows = cell(0, 3);
if ~isfolder(stages)
    rows(end+1, :) = {'SKIPPED', 'stages vs ROS 2', sprintf('no %s (run scripts/make_matlab_stages.py)', stages)}; return
end
rd = @(name) readmatrix(fullfile(stages, name));
feat = rd('decoder_input.csv');
D = {'lda', 'r2n_linear_predict (LDA)', @r2n_linear_read, @r2n_linear_predict
     'svm', 'r2n_linear_predict (SVM)', @r2n_linear_read, @r2n_linear_predict
     'qda', 'r2n_qda_predict (QDA)',    @r2n_qda_read,    @r2n_qda_predict};
for i = 1:size(D, 1)
    f = dir(fullfile(stages, 'models', D{i, 1}, '*.r2nd')); m = D{i, 3}(fullfile(f(1).folder, f(1).name));
    y = zeros(size(feat, 1), m.n_classes);
    for r = 1:size(feat, 1), y(r, :) = D{i, 4}(m, feat(r, :)); end
    rows(end+1, :) = compare_stage(D{i, 2}, rd(['decoder_' D{i, 1} '.csv']), y, 4); %#ok<AGROW>
end
pred = rd('integrator_input.csv');
rows(end+1, :) = compare_stage('r2n_integrator_buffer hard (10)', rd('integrator_buffer_hard.csv'), r2n_integrator_buffer(pred, 10, 0), 4);
rows(end+1, :) = compare_stage('r2n_integrator_buffer soft (10)', rd('integrator_buffer_soft.csv'), r2n_integrator_buffer(pred, 10, 1), 4);
x = single(rd('spectral_input.csv')); blk = 32; fs = 512;
ros = rd('fft.csv'); y = zeros(size(ros, 1), size(ros, 2) - 1);
for r = 1:size(ros, 1)
    e = ros(r, 1) * blk; a = r2n_fft(x(e-255:e, :), fs, 'hann', false); y(r, :) = a(:)';
end
rows(end+1, :) = compare_stage('r2n_fft (256, hann)', ros(:, 2:end), y, 4);
ros = rd('spectrogram.csv'); y = zeros(size(ros, 1), size(ros, 2) - 1);
for r = 1:size(ros, 1)
    e = ros(r, 1) * blk; p = r2n_spectrogram(x(e-511:e, :), fs, 128, 64, 'hamming', true); y(r, :) = reshape(permute(p, [3 2 1]), 1, []);
end
rows(end+1, :) = compare_stage('r2n_spectrogram (128/64 of 512, hamming, dB)', ros(:, 2:end), y, 4);
end

function row = compare_stage(name, ros, y, ulps)
if ~isequal(size(ros), size(y))
    row = {'FAIL', name, sprintf('ROS 2 gave %dx%d values, the function %dx%d', size(ros), size(y))}; return
end
d = abs(ros - double(y)); m = max(d(:)); tol = ulps * double(eps(single(max(abs(ros(:))))));
status = 'PASS'; if ~(m <= tol), status = 'FAIL'; end
row = {status, name, sprintf('max error %-9.3g (tolerance %.3g = %d ULP of the largest value %.4g), %d values', m, tol, ulps, max(abs(ros(:))), numel(d))};
end
