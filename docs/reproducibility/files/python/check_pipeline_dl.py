#!/usr/bin/env python3
"""Test 6, whole pipeline with a deep-learning model: ROS 2 against Python, step by step.

    python3 check_pipeline_dl.py [run_folder]        # in the container (needs torch, braindecode, scipy, matplotlib); default: the newest run of runs/

The run (pipeline_dl.launch.py) saved the raw frames, the output of the band-pass, some Buffer windows, the prediction of the network, the integrator output, the flow of
the feedback and the events. Python redoes the chain from the RAW frames of the run, with code that is not the plugins':
  1. band-pass:   scipy.signal.butter + lfilter (causal, state kept, double precision), hp 4 Hz then lp 14 Hz, order 2 (config/shallow_pipeline.yaml)
  2. buffer:      the last 512 samples of the filtered signal
  3. network:     braindecode ShallowFBCSPNet of the manifest, in eval mode on CPU, on every window (16 channels picked by label)
  4. integrator:  exponential, state = alpha * state + (1 - alpha) * p, reset to 1/K at every CFeedback (alpha in config/integrator_exponential.yaml)
  5. control:     the integrated values normalized (v / sum): the flow the feedback window draws
and compares every step with what ROS 2 published (PASS / FAIL lines like check_*.m), plus the network alone on the windows ROS 2 saved. One figure per step (ROS 2 and
Python above, their difference below, time axes linked). Exits with 1 if a check fails.
"""
import csv
import glob
import importlib
import json
import os
import re
import sys

import matplotlib
if not os.environ.get('DISPLAY') or os.environ.get('NO_SHOW'):
    matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import torch
import yaml
from scipy.signal import butter, lfilter

HERE = os.path.dirname(os.path.abspath(__file__))
PKG = HERE
while not os.path.isfile(os.path.join(PKG, 'package.xml')):
    PKG = os.path.dirname(PKG)
CFG = os.path.join(HERE, 'config')
rows = []


def report(name, ok, note=''):
    rows.append(bool(ok))
    print('  %-4s  %-52s %s' % ('PASS' if ok else 'FAIL', name, note))


def read_csv(path):
    with open(path) as f:
        reader = csv.reader(f)
        header = next(reader)
        data = np.array([[float(x) for x in row] for row in reader])
    return header, data


def stamps(d):
    return np.array([int(r[2]) * 10 ** 9 + int(r[3]) for r in d], dtype=np.int64)


def newest_run(folder):
    latest = os.path.join(folder, 'latest.txt')
    if os.path.isfile(latest):
        return os.path.join(folder, open(latest).read().strip())
    runs = sorted(glob.glob(os.path.join(folder, 'run_*')))
    if not runs:
        sys.exit('no run in %s: launch the test first (see README.md)' % folder)
    return runs[-1]


def find_model():
    for base in os.environ.get('AMENT_PREFIX_PATH', '').split(':'):
        c = os.path.join(base, 'share', 'ros2neuro_decoder_braindecode', 'extra', 'eegnet_mi_bhbf')
        if os.path.isfile(os.path.join(c, 'manifest.yaml')):
            return c
    return os.path.join(PKG, '..', 'ros2neuro_decoder_braindecode', 'extra', 'eegnet_mi_bhbf')


def section(path, node):
    """The parameters of one node of a parameter file."""
    return yaml.safe_load(open(path))['/' + node]['ros__parameters']


def figure(name, title, t, ros, mine, col, tol, axes, label):
    """Above: ROS 2 and Python; below: their difference. The x axes of every figure are shared (zoom one: they all follow)."""
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(11, 6.5), sharex=not axes)
    if axes:                                                            # share the time axis with the first figure (and between the two plots)
        a1.sharex(axes[0]); a2.sharex(a1)
    a1.plot(t, mine[:, col], 'b-', lw=1.5, label='Python')
    a1.plot(t, ros[:, col], 'r--', lw=1, label='ros2neuro (recorded)')
    a1.set_title('step %s: %s' % (name, label)); a1.set_ylabel('value'); a1.grid(True); a1.legend()
    a2.plot(t, ros[:, col] - mine[:, col], 'k-', label='ros2neuro - Python (that column)')
    a2.plot(t, np.max(np.abs(ros - mine), axis=1), 'm:', label='largest |difference| over all columns')
    a2.set_title('difference (tolerance %.3g)' % tol); a2.set_xlabel('time (s)'); a2.set_ylabel('difference'); a2.grid(True); a2.legend()
    fig.tight_layout()
    axes.append(a1)
    fig.savefig(os.path.join(RUN, 'figure_pipeline_dl_%s.png' % name.replace(' ', '_')))
    return fig


def compare(name, ros, mine, tol, t, col, label, axes, note=''):
    ros, mine = np.asarray(ros, dtype=np.float64), np.asarray(mine, dtype=np.float64)
    if ros.shape != mine.shape:
        report('chain step ' + name, False, 'ROS 2 gave %s values, Python %s' % (ros.shape, mine.shape))
        return
    err = np.abs(ros - mine)
    worst = float(err.max()) if err.size else 0.0
    report('chain step ' + name, worst <= tol, '%d rows x %d columns, max |ROS - Python| = %.3g (tolerance %.3g)%s' % (ros.shape[0], ros.shape[1], worst, tol, note))
    figure(name, label, t, ros, mine, col, tol, axes, label)


def main():
    global RUN
    folder = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, 'runs')
    RUN = folder if os.path.isfile(os.path.join(folder, 'raw.csv')) else newest_run(folder)
    model_dir = find_model()
    print('\nTest 6, whole pipeline, ShallowNet: ROS 2 against Python\n  run %s\n  model %s\n' % (RUN, model_dir))
    axes = []

    # ---- the data ROS 2 saved
    rh, rd = read_csv(os.path.join(RUN, 'raw.csv'))
    eeg = [i for i in range(5, len(rh)) if not rh[i].startswith('trigger:')]           # the EEG columns (not the trigger channels)
    labels_raw = [rh[i] for i in eeg]
    raw = rd[:, eeg].astype(np.float32)                                 # [samples, channels]
    raw_stamp = stamps(rd)
    hop = int(rd[:, 4].max()) + 1                                       # samples per frame
    fs = 512.0
    frame_stamp = raw_stamp[::hop]
    fh, fd = read_csv(os.path.join(RUN, 'filtered.csv'))
    filt, filt_stamp = fd[:, [i for i in range(5, len(fh)) if not fh[i].startswith('trigger:')]].astype(np.float32), stamps(fd)
    bh, bd = read_csv(os.path.join(RUN, 'buffer.csv'))
    buf_labels = bh[4:]
    ph, pdata = read_csv(os.path.join(RUN, 'prediction.csv'))
    pred, pred_stamp = pdata[:, 5:].astype(np.float32), stamps(pdata)
    ih, idata = read_csv(os.path.join(RUN, 'integrated.csv'))
    integ, integ_stamp = idata[:, 5:].astype(np.float32), stamps(idata)
    wh, wdata = read_csv(os.path.join(RUN, 'flow.csv'))
    flow, flow_stamp = wdata[:, 5:].astype(np.float32), stamps(wdata)
    eh, edata = read_csv(os.path.join(RUN, 'events.csv'))
    ids = edata[:, 4].astype(int)
    K = pred.shape[1]
    meta = json.load(open(os.path.join(RUN, 'meta.json')))
    buf_shape = meta['streams']['buffer']['feature']['shape']
    buf_labels = meta['streams']['buffer']['feature']['axes'][1]['labels']

    # ---- the session (events of the manager and of control)
    layout = yaml.safe_load(open(os.path.join(CFG, 'layout.yaml')))['/**']['ros__parameters']
    protocol = yaml.safe_load(open(os.path.join(CFG, 'protocol_evaluation.yaml')))
    trials = protocol['/manager']['ros__parameters']['trials']
    starts = np.where(ids == 1)[0]
    report('number of trials', len(starts) == sum(trials), '%d Start events, protocol trials %s' % (len(starts), trials))
    ok = True
    for i in starts:
        s = ids[i:i + 10]
        ok &= len(s) == 10 and list(s[[0, 1, 2, 3, 6, 7]]) == [1, 1 + 32768, 786, 786 + 32768, 781, 781 + 32768] and s[4] in layout['classes'] and s[8] in (897, 898, 899)
    report('sequence of every trial', ok, 'Start, Fixation, cue, CFeedback, then Hit / Miss / Timeout, each closed by its Off')

    # ---- 1. band-pass: scipy butter + lfilter on the RAW frames, from the first frame the node received
    cfgp = os.path.join(CFG, 'shallow_pipeline.yaml')
    fp = section(cfgp, 'filters')
    first = int(np.where(frame_stamp == filt_stamp[0])[0][0]) if filt_stamp[0] in frame_stamp else None
    report('filtered: same frames as the input', first is not None and np.array_equal(filt_stamp, raw_stamp[first * hop:first * hop + len(filt_stamp)]),
           'first frame received: %s' % (None if first is None else first + 1))
    off = first * hop
    n = len(filt)
    mine = raw[off:off + n].astype(np.float64)
    for name in fp['filters.chain']:
        b, a = butter(fp['filters.%s.order' % name], fp['filters.%s.cutoff' % name] / (fp['filters.%s.samplerate' % name] / 2),
                      btype='high' if fp['filters.%s.type' % name] == 'highpass' else 'low')
        mine = lfilter(b, a, mine, axis=0)
    ulp = float(np.spacing(np.float32(np.abs(raw).max())))
    col = labels_raw.index('Cz') if 'Cz' in labels_raw else 8
    t_samples = (off + np.arange(n)) / fs
    compare('1 band-pass', filt, mine, 16 * ulp, t_samples, col, 'Cz after hp 4 Hz + lp 14 Hz (scipy butter + lfilter)', axes)
    filt_py = mine                                                      # filt_py[j] is the sample off + j of the run

    # ---- 2. the Buffer windows ROS 2 saved against the last 512 samples of the Python signal
    window = buf_shape[0]
    kfb = np.array([int(np.where(frame_stamp == s)[0][0]) + 1 for s in stamps(bd)])
    wins_py, wins_ros, tb = [], [], []
    for r, k in zip(bd, kfb):
        last = k * hop
        if last - window - off < 0:
            continue                                                     # a window that starts before the filter node did (zeros in ROS 2)
        wins_py.append(filt_py[last - window - off:last - off].reshape(1, -1)[0])
        wins_ros.append(r[4:])
        tb.append(last / fs)
    compare('2 buffer window', np.array(wins_ros), np.array(wins_py), 16 * ulp, np.array(tb), 0, 'first value of every saved 512 x %d window' % len(buf_labels), axes)

    # ---- 3. the network (braindecode / PyTorch) on EVERY window of the Python signal
    manifest = yaml.safe_load(open(os.path.join(model_dir, 'manifest.yaml')))
    dec = manifest['decoder']
    module_name, class_name = dec['target'].rsplit('.', 1)
    cls = getattr(importlib.import_module(module_name), class_name)
    net = cls.from_config(dec['config']) if hasattr(cls, 'from_config') else cls(**dec['config'])
    net.load_state_dict(torch.load(os.path.join(model_dir, dec.get('parameters_file', 'params.pt')), map_location='cpu', weights_only=True))
    net.eval()
    labels = [str(c) for c in manifest['input']['axes'][1]['labels']]
    fields = [str(c) for c in manifest['output']['fields']]
    report('output fields are the classes of the model', [str(c) for c in ph[5:]] == fields, ' '.join(ph[5:]))
    pick = [buf_labels.index(c) for c in labels]

    def probabilities(window_rows):
        """Probabilities of the network for windows [n, samples, channels of the buffer]."""
        with torch.no_grad():
            out = net(torch.tensor(window_rows[:, :, pick].transpose(0, 2, 1), dtype=torch.float32)).double()
            p = torch.exp(out)
            return (p if abs(float(p.sum(1).mean()) - 1.0) < 1e-4 else torch.softmax(out, dim=1)).numpy()

    # the network alone on the windows ROS 2 saved
    sp = {s: i for i, s in enumerate(pred_stamp)}
    keep = [i for i, s in enumerate(stamps(bd)) if s in sp]
    alone = probabilities(bd[keep, 4:].reshape(len(keep), window, len(buf_labels)).astype(np.float32))
    worst = float(np.abs(alone - pred[[sp[stamps(bd)[i]] for i in keep]]).max())
    report('network alone, fed with the ROS 2 windows', worst <= 1e-5, 'max |difference| = %.3g over %d windows (tolerance 1e-05)' % (worst, len(keep)))
    # the whole chain: a window for every prediction
    kp = np.array([int(np.where(frame_stamp == s)[0][0]) + 1 for s in pred_stamp])
    ok_rows = [i for i, k in enumerate(kp) if k * hop - window - off >= 0]
    wins = np.stack([filt_py[kp[i] * hop - window - off:kp[i] * hop - off] for i in ok_rows]).astype(np.float32)
    mine_p = np.zeros_like(pred, dtype=np.float64)
    mine_p[ok_rows] = probabilities(wins)
    compare('3 network', pred[ok_rows], mine_p[ok_rows], 1e-3, kp[ok_rows] * hop / fs, 0, 'probability of the first class', axes)

    # ---- 4. integrator (exponential): resets where ROS 2 made them (a neutral message repeats the stamp of the one before it)
    ip = section(os.path.join(CFG, 'integrator_exponential.yaml'), 'integrator')
    alpha = float(ip['integrator.params.alpha'])
    neutral = np.concatenate([[False], integ_stamp[1:] == integ_stamp[:-1]])
    real = np.where(~neutral)[0]
    j0 = int(np.where(pred_stamp == integ_stamp[real[0]])[0][0])         # the integrator may miss the first predictions: its state starts at the first one it received
    report('every prediction was integrated, in order', np.array_equal(integ_stamp[real], pred_stamp[j0:]),
           '%d predictions, %d integrated values + %d neutral (reset) messages; first integrated: prediction %d' % (len(pred), len(real), int(neutral.sum()), j0 + 1))
    report('one reset per CFeedback', int(neutral.sum()) == int((ids == 781).sum()), '%d resets, %d CFeedback events' % (int(neutral.sum()), int((ids == 781).sum())))
    resets = set(int(np.sum(~neutral[:r])) for r in np.where(neutral)[0])   # index of the first prediction after each reset

    def integrate(p):
        out, state = np.zeros_like(p, dtype=np.float64), None
        for k in range(len(p)):
            if k in resets:
                state = np.full(K, 1.0 / K)
            state = p[k].astype(np.float64) if state is None else alpha * state + (1 - alpha) * p[k]
            out[k] = state
        return out

    alone_i = integrate(pred[j0:])
    err = float(np.abs(integ[real] - alone_i).max())
    report('integrator alone, fed with the ROS 2 predictions', err <= 1e-6, 'max |ROS - Python| = %.3g (tolerance 1e-06)' % err)
    chain_i = alone_i.copy()
    okr = [i - j0 for i in ok_rows if i >= j0]                          # rows of the integrated values whose window the Python chain could build
    feed = pred.astype(np.float64).copy()                               # the Python probabilities where Python had a window, the ROS 2 ones before the buffer was full
    feed[ok_rows] = mine_p[ok_rows]
    chain_i[okr] = integrate(feed[j0:])[okr]
    compare('4 integrator', integ[real][okr], chain_i[okr], 1e-3, np.array([kp[i + j0] * hop / fs for i in okr]), 0, 'first class', axes)

    # ---- 5. control: the integrated values normalized: the flow the window draws
    match = {s: i for i, s in enumerate(pred_stamp)}
    fidx = [(j, match[s] - j0) for j, s in enumerate(flow_stamp) if s in match and match[s] >= j0 and match[s] - j0 in set(okr)]
    flow_ros = flow[[j for j, _ in fidx], :K]
    flow_py = np.array([chain_i[i] / chain_i[i].sum() for _, i in fidx])
    compare('5 control flow', flow_ros, flow_py, 1e-3, np.array([kp[i + j0] * hop / fs for _, i in fidx]), 0, 'normalized value of the first class (what the window draws)', axes)
    thr = np.array(layout['thresholds'])
    report('the flow carries the thresholds of the layout', bool(np.all(np.abs(flow[:, K:] - thr) < 1e-6)), 'thresholds %s' % thr.tolist())

    failed = rows.count(False)
    print('\ncheck_pipeline_dl.py: %d checks, %d passed, %d failed' % (len(rows), len(rows) - failed, failed))
    plt.show()
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
