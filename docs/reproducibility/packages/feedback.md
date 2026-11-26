# Feedback: tests and replication

!!! info ""
    Plugins: [Feedback](../../packages/feedback/index.md) · part of [Reproducibility](../index.md) › [Packages](index.md)

How the feedback is checked: the feedback windows are **to be looked at**: the complete pipelines of `feedback/` open the wheel and the bars; the flow they draw is checked in the [pipeline tests](../pipeline.md).

| Test (`ros2neuro_devel_test`) | What it checks | Check | MATLAB functions | Python functions |
|---|---|---|---|---|
| `feedback/wheel/` `bars2/` `bars4/` | the windows (nothing is saved or checked) | none | none | none |

How to run a test: [Packages](index.md#run-the-checks). Every function is explained, with its code, in [MATLAB](../matlab.md) and [Python](../python.md); [download them](../download.md).

## Feedback (base package)

### Tests of the whole stack

[`ros2neuro_devel_test`](https://github.com/ros2neuro/ros2neuro_devel_test) (`feedback/ and pipeline/`) shows the wheel and the bars (2 and 4 classes) driven by the whole chain from a GDF. It is the test to run **on a new computer after installing**: if the window opens and moves through the trials, the install works. The `pipeline/` tests also check, in MATLAB, the flow that the window draws. Run: `feedback/wheel/feedback_wheel.launch.py` and `feedback/bars4/feedback_bars4.launch.py` (to be looked at); `pipeline/<name>/pipeline_<name>.launch.py` then `check_pipeline_<name>`; the check is a MATLAB file you read from the top (see the README of that package).

## neurodraw

```bash
ctest --test-dir build --output-on-failure
```

The test suite currently covers:

- shape geometry and transforms
- hit testing and grouping
- tween progression
- text and image layout metrics
- `neurochrono` timing utilities
- a CMake package-consumer smoke test
