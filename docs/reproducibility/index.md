# Reproducibility

**Reproducibility** means being able to take a recording, run it again **offline**, step by step, and obtain the numbers ROS2neuro computed online. If you can redo every stage on your own, you can check a result, repeat a run, find where two runs diverge and write the analysis of an experiment with the same numbers the real-time system gave. It is also how the stack is tested: every stage is compared with its replica, and the comparison is repeated on the same data every time you run it.

## What is reproduced

The **whole chain**, from the samples of the amplifier to the value that moves the feedback window:

```text
raw EEG → filters → processing (Welch, FFT, spectrogram, FBCSP) → decoder → integrator → control (Hit / Miss / Timeout)
```

Every stage has a **test** that replays a GDF file through the real nodes and a **check** that redoes the stage offline and compares: PASS / FAIL for every line, and a figure with the replica and ros2neuro on top of each other and their difference. The figures of the integrator and of the control flow also show the threshold and every trial as a band (green Hit, red Miss, grey Timeout).

## In which language

The replication is written in **two languages**, with the same function names, so you can use the one you work in:

| | MATLAB | Python |
|---|---|---|
| Functions | one `r2n_*.m` per stage, built on the **native MATLAB functions** (`butter`, `pwelch`, `hann`, ...) | the same `r2n_*.py`, built on numpy and scipy |
| Models it can open | the `.r2nd` of the decoders (LDA, QDA, SVM, Gaussian) and the numbers of a scikit-learn LDA | the `.r2nd`, **any scikit-learn model** (skops) and **any deep-learning model** (braindecode / PyTorch) |
| Use it for | every model that is not a neural network | everything, in particular the machine-learning and deep-learning decoders |

## What is in this menu

| Page | What you find |
|---|---|
| [Packages](packages/index.md) | the tests of every package and plugin, one page per package (acquisition, filters, processing, decoder, integrator, control, manager, feedback, visualizer), how a test is built and run, how close each stage is to its replica |
| [Pipeline](pipeline.md) | the **complete** pipelines (QDA, LDA, FBCSP + LDA, deep learning) with the feedback window, the figure of the flow and how to replay it step by step in MATLAB and in Python |
| [MATLAB](matlab.md) | the table of the `r2n_*.m` functions: click a name and its dropdown opens, with the explanation of what it does, how it matches the plugin and its code |
| [Python](python.md) | the same table for `r2n_*.py`, with the loaders of the `.r2nd`, scikit-learn and braindecode models |
| [Download](download.md) | the two zips and how to run the functions on your own data |

## Where to start

* To **check a plugin** you changed: [Packages](packages/index.md), the page of its package.
* To **see the whole chain** agree with the replica, and the figure it ends with: [Pipeline](pipeline.md).
* To **reuse a function in your own analysis**, or open a trained model offline: [MATLAB](matlab.md) or [Python](python.md), then [Download](download.md).
