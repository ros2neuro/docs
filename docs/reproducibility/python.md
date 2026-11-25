# Reproducibility in Python

A deep network cannot be redone with the MATLAB functions. Its pipeline is replayed in **Python**, with code that is not the plugins': `scipy` for the filter, `braindecode` / `PyTorch` for the network, `numpy` for the integrator, and compared with what ROS 2 published.

!!! success "Download"
    **[check_pipeline_dl.py](files/python/check_pipeline_dl.py)** (also in `pipeline/dl/` of [`ros2neuro_devel_test`](https://github.com/ros2neuro/ros2neuro_devel_test/tree/main/pipeline/dl)); the network alone is also checked by `decoder/shallow/check_decoder_shallow.py`.

## The pipeline

raw frames → band-pass 4-14 Hz (Butterworth, order 2) → Buffer (512 samples) → ShallowNet (braindecode) → exponential integrator → control (the flow the feedback window draws).

| Step | In ROS 2 | In Python |
|---|---|---|
| band-pass | `filter_chain_node` with two Butterworth filters | `scipy.signal.butter` + `lfilter` (causal, state kept, double precision) |
| window | `Buffer` plugin | the last 512 samples of the filtered signal |
| network | `decoder_braindecode` (embedded Python) | the model of the manifest, `eval()` on CPU, on every window |
| integrator | `integrator_exponential` | `state = alpha * state + (1 - alpha) * p`, reset to 1/K at every CFeedback |
| control | `control_feedback` | the integrated values divided by their sum |

## Run it

```bash
# in the container: the session (about 3.5 minutes, with the feedback window), then the check
ros2 launch ~/ros2neuro_ws/src/ros2neuro_devel_test/pipeline/dl/pipeline_dl.launch.py
python3 ~/ros2neuro_ws/src/ros2neuro_devel_test/pipeline/dl/check_pipeline_dl.py
```

It prints PASS / FAIL for every step and draws one figure per step (ROS 2 and Python above, their difference below, with linked time axes). It exits with 1 if a step fails.

## The code

??? example "check_pipeline_dl.py"
    ```python
    --8<-- "files/python/check_pipeline_dl.py"
    ```
