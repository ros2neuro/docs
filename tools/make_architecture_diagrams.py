#!/usr/bin/env python3
"""Four schematic figures of ros2neuro (Graphviz).

  python3 make_architecture_diagrams.py OUT_DIR      -> OUT_DIR/ros2neuro_1_overview.{png,svg}, _2_topics, _3_services, _4_parameters

1 overview    : the main packages (parent name) and what is connected to what
2 topics      : + the plugins of each package, + the topic and the message type on every arrow
3 services    : + the service calls (there are no ROS actions in the stack)
4 parameters  : which parameters every node reads: its own, and the global ones (`/**`) shared by several nodes. Nobody asks anybody
"""
import subprocess, sys, os

BLUE = ('#e3f0fb', '#2a6ca3'); GREEN = ('#e8f5e3', '#3d8b2e'); PURPLE = ('#f3e8fb', '#7a3fa3')
RED = ('#fbe9ee', '#a3314f'); ORANGE = ('#ffd9b3', '#c25a00'); GREY = ('#eeeeee', '#888888')
SVC = dict(style='dashed', color='#1b6b8f', fontcolor='#1b6b8f', penwidth='2.4')
ORG = dict(color='#c25a00', fontcolor='#7a3a00')

def box(title, colors, sub='', lines=(), head='plugins', size=20):
    fill, border = colors
    rows = [f'<TR><TD BGCOLOR="{border}"><FONT COLOR="white" POINT-SIZE="{size}"><B>{title}</B></FONT></TD></TR>']
    if sub:
        rows.append(f'<TR><TD><FONT POINT-SIZE="13">{sub}</FONT></TD></TR>')
    if lines and head:
        rows.append(f'<TR><TD ALIGN="LEFT"><FONT POINT-SIZE="11" COLOR="#555555"><I>{head}</I></FONT></TD></TR>')
    if lines:
        for l in lines:
            rows.append(f'<TR><TD ALIGN="LEFT" BGCOLOR="white"><FONT POINT-SIZE="12">&#8226; {l}</FONT></TD></TR>')
    return (f'<<TABLE BORDER="3" COLOR="{border}" CELLBORDER="0" CELLSPACING="2" CELLPADDING="7" BGCOLOR="{fill}">'
            + ''.join(rows) + '</TABLE>>')

def build(n):
    L = []
    titles = {1: ('ROS2neuro, overview', 'the main packages and what is connected to what'),
              2: ('ROS2neuro, topics', 'plugins of each package; solid arrow = topic (name, <B>message type</B>)'),
              3: ('ROS2neuro, services', 'as the topics figure, plus the service calls (blue dashed). The stack has no ROS actions; no node asks another one for parameters'),
              4: ('ROS2neuro, parameters', 'every node reads its own parameters; what several nodes share is one global (<B>/**</B>) section that each of them loads. Nobody asks anybody')}[n]
    L.append('digraph g {')
    L.append(f'  graph [rankdir=TB, nodesep=0.6, ranksep=1.4, fontname="Helvetica", pad=0.5, newrank=true, labelloc=t, '
             f'label=<<FONT POINT-SIZE="34"><B>{titles[0]}</B></FONT><BR/><FONT POINT-SIZE="16">{titles[1]}</FONT>>];')
    L.append('  node [shape=plain, fontname="Helvetica"]; edge [fontname="Helvetica", fontsize=14, color="#333333", penwidth=2.4, arrowsize=1];')
    def e(a, b, label='', **kw):
        at = ', '.join(f'{k}="{v}"' for k, v in kw.items())
        L.append(f'  {a} -> {b} [label=<{label if n > 1 else ""}>{", " + at if at else ""}];')
    def n_(name, label):
        L.append(f'  {name} [label={label}];')
    def grey(name, label):
        L.append(f'  {name} [shape=box, style="rounded,filled", fillcolor="#eeeeee", color="#888888", fontsize=15, label=<{label}>];')

    if n == 4:
        n_('glob', box('global parameters  /**', ORANGE, 'one section of the parameter file (layout.yaml), loaded by every node that needs it', [
            'classes, rest_mode',
            'thresholds  (initial; changeable while running on /control)',
            'event.start / fixation / cfeedback / hit / miss / timeout / off / shown  (defaults of the stack)'], 'the same value for everyone', size=20))
        n_('man', box('ros2neuro_manager', RED, 'node <B>/manager</B>, plugin Synchronous / Asynchronous', [
            'reads: classes, rest_mode, event.*', 'own: trials, duration.begin / start / fixation / cue / boom / iti / end / outcome_wait',
            'own: protocol_ended_topic, shutdown_on_end'], ''))
        n_('ctl', box('ros2neuro_control', ORANGE, 'node <B>/control</B>, plugin control_feedback', [
            'reads: classes, rest_mode, event.*, thresholds', 'own: protocol (calibration | evaluation | control), input_fields',
            'own: duration.feedback_min / feedback_max / timeout, rest_timeout', 'own: input_topic, reset_service, control_topic'], ''))
        n_('fbk', box('ros2neuro_feedback', RED, 'node <B>/feedback</B>, plugin Wheel / Bar', [
            'reads: classes, rest_mode, event.*, thresholds (the first markers)', 'own: plugin, fps, window_title, publish_display_events'], ''))
        grey('user', '<B>operator</B><BR/>ros2 param set /control thresholds')
        n_('rest', box('written in several places (no global section yet)', GREY, 'the same value in several yaml sections: see the list of shared parameters', [
            'event_topic (/neuroevent): manager, control, feedback, integrator, recorder',
            'integrator.reset_event = event.cfeedback (781)',
            'topic names of every link of the chain',
            'sensor name, sample rate, channels, frequencies: acquisition, filters, processing, decoder model'], '', size=18))
        e('glob', 'man', 'loaded: classes, rest_mode, event.*', color='#c25a00', fontcolor='#7a3a00', penwidth='2.4', style='dashed')
        e('glob', 'ctl', 'loaded: classes, rest_mode, event.*, thresholds', color='#c25a00', fontcolor='#7a3a00', penwidth='2.4', style='dashed')
        e('glob', 'fbk', 'loaded: classes, rest_mode, event.*, thresholds', color='#c25a00', fontcolor='#7a3a00', penwidth='2.4', style='dashed')
        e('ctl', 'fbk', 'thresholds in force travel in the flow<BR/>(NeuroControl on /control_feedback/probabilities)', color='#c25a00', fontcolor='#7a3a00', penwidth='2.4')
        e('user', 'ctl', 'ros2 param set<BR/>(thresholds, at run time)', color='#888888', fontcolor='#555555', penwidth='2.4')
        L.append('  { rank=same; man; ctl; fbk; }')
        L.append('  man -> ctl [style=invis, weight=50]; ctl -> fbk [style=invis, weight=50];')
        L.append('  { rank=same; user; rest; }')
        L.append('  user -> rest [style=invis];')
        L.append('}')
        return '\n'.join(L)

    full = n >= 2
    grey('hw', '<B>EEG amplifier</B><BR/>or GDF file')
    if full:
        n_('acq', box('ros2neuro_acquisition', BLUE, '', ['Dummy, LSL, EEGdev', 'ANT eego, g.USBamp, XDF']))
        n_('fil', box('ros2neuro_filters', BLUE, '', ['dc, butterworth, car, laplacian', 'hann, hamming, blackman, flattop']))
        n_('pro', box('ros2neuro_processing', BLUE, '', ['welch, fft, spectrogram, buffer'], 'nodes (no plugins)'))
        n_('dec', box('ros2neuro_decoder', GREEN, '', ['LDA, QDA, SVM, Gaussian', 'deep learning (PyTorch)']))
        n_('intg', box('ros2neuro_integrator', GREEN, '', ['Exponential, Buffer']))
        n_('ctl', ('<<TABLE BORDER="3" COLOR="#c25a00" CELLBORDER="0" CELLSPACING="2" CELLPADDING="7" BGCOLOR="#ffd9b3">'
                    '<TR><TD BGCOLOR="#c25a00"><FONT COLOR="white" POINT-SIZE="20"><B>ros2neuro_control</B></FONT></TD></TR>'
                    '<TR><TD ALIGN="LEFT"><FONT POINT-SIZE="11" COLOR="#555555"><I>plugins</I></FONT></TD></TR>'
                    '<TR><TD ALIGN="LEFT" BGCOLOR="white"><FONT POINT-SIZE="12">&#8226; control_feedback (Feedback)</FONT></TD></TR>'
                    '<TR><TD ALIGN="LEFT" BGCOLOR="#fff7ee" BORDER="1" STYLE="dashed" COLOR="#c25a00"><FONT POINT-SIZE="12" COLOR="#7a3a00"><I>&#8226; control_robot  (yours:<BR ALIGN="LEFT"/>&#160;&#160;the code that connects a robot)</I></FONT></TD></TR>'
                    '</TABLE>>'))
        n_('man', box('ros2neuro_manager', RED, '', ['Synchronous, Asynchronous']))
        n_('fbk', box('ros2neuro_feedback', RED, '', ['Wheel, Bar']))
        n_('rec', box('ros2neuro_recorder', PURPLE, '', ['XDFRecorder']))
        n_('viz', box('ros2neuro_visualizer', PURPLE, 'scope of the signals'))
    else:
        for k, t, c in [('acq', 'acquisition', BLUE), ('fil', 'filters', BLUE), ('pro', 'processing', BLUE), ('dec', 'decoder', GREEN),
                        ('intg', 'integrator', GREEN), ('ctl', 'control', ORANGE), ('man', 'manager', RED), ('fbk', 'feedback', RED),
                        ('rec', 'recorder', PURPLE), ('viz', 'visualizer', PURPLE)]:
            n_(k, box('ros2neuro_' + t, c, size=22))
    if full:
        L.append('  bus [shape=cds, style=filled, fillcolor="#fff3c4", color="#b8860b", penwidth=3, fontsize=18, label=<<B>/neuroevent</B><BR/><FONT POINT-SIZE="14">event bus (<B>NeuroEvent</B>)</FONT>>];')

    e('hw', 'acq', '', weight='10')
    e('acq', 'fil', '/acquisition/neurodata<BR/><B>NeuroFrame</B>')
    e('fil', 'pro', '/processing/filtered<BR/><B>NeuroFrame</B>')
    e('pro', 'dec', '/processing/psd<BR/><B>NeuroFeature</B>')
    e('dec', 'intg', '/classification/prediction<BR/><B>NeuroPrediction</B>')
    e('intg', 'ctl', '/integrated/raw<BR/><B>NeuroPrediction</B>', **ORG)
    e('ctl', 'fbk', '/control_feedback/probabilities<BR/><B>NeuroControl</B> (values, thresholds)', **ORG)
    e('acq', 'rec', '/acquisition/neurodata<BR/><B>NeuroFrame, NeuroFrameInfo</B>' if full else '', color='#7a3fa3', fontcolor='#7a3fa3')
    e('acq', 'viz', '/acquisition/neurodata<BR/><B>NeuroFrame</B>' if full else '', color='#7a3fa3', fontcolor='#7a3fa3')
    if full:
        e('bus', 'man', 'manager writes the phases,<BR/>hears the outcome', dir='both', color='#a3314f', fontcolor='#a3314f')
        e('bus', 'ctl', 'control hears the cue,<BR/>writes Hit / Miss / Timeout', dir='both', **ORG)
        e('rec', 'bus', '<B>NeuroEvent</B>', dir='back')
        e('bus', 'intg', 'reset event', constraint='false', color='#888888', fontcolor='#555555')
        e('bus', 'fbk', 'the feedback hears: fixation, cue,<BR/>outcome (display events: optional)', dir='both', constraint='false', color='#a3314f', fontcolor='#a3314f')
    else:
        e('man', 'ctl', dir='both', color='#a3314f')
        e('man', 'rec', color='#a3314f')
        e('ctl', 'rec', constraint='false', color='#c25a00')
    if n == 3:
        grey('user', '<B>operator</B>')
        e('user', 'acq', '<B>start / stop / quit</B>', **SVC)
        e('ctl', 'intg', '<B>/reset</B>', constraint='false', **SVC)
        L.append('  { rank=min; user; }')
    L.append('  { rank=same; hw; acq; fil; pro; dec; intg; }')
    if full:
        L.append('  { rank=same; viz; rec; bus; ctl; }')
        L.append('  { rank=same; man; fbk; }')
        L.append('  viz -> rec [style=invis, weight=50]; rec -> bus [style=invis, weight=50]; bus -> ctl [style=invis, weight=50]; man -> fbk [style=invis, weight=50];')
        L.append('  bus -> man [style=invis, weight=60]; ctl -> fbk [style=invis, weight=60];')
    else:
        L.append('  { rank=same; man; ctl; }')
        L.append('  { rank=same; viz; rec; fbk; }')
        L.append('  man -> ctl [style=invis, weight=50]; viz -> rec [style=invis, weight=50]; rec -> fbk [style=invis, weight=50];')
    L.append('}')
    return '\n'.join(L)

def main(out):
    os.makedirs(out, exist_ok=True)
    for n, name in [(1, 'overview'), (2, 'topics'), (3, 'services'), (4, 'parameters')]:
        base = os.path.join(out, f'ros2neuro_{n}_{name}')
        open(base + '.dot', 'w').write(build(n))
        subprocess.run(['dot', '-Tpng', '-Gdpi=110', base + '.dot', '-o', base + '.png'], check=True)
        subprocess.run(['dot', '-Tsvg', base + '.dot', '-o', base + '.svg'], check=True)
        os.remove(base + '.dot')
        print(base + '.png')

if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else '.')
