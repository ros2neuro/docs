# Install from the apt repository

The quickest way: no compiler needed.



## Install the repository and the packages

[ROS 2 Jazzy](https://docs.ros.org/en/jazzy/Installation.html) must already be installed.

=== "1. Add the repository"

    ```bash
    curl -fsSL https://ros2neuro.github.io/ppa/ubuntu/ros2neuro-key.asc | gpg --dearmor | sudo tee /etc/apt/trusted.gpg.d/ros2neuro-key.gpg > /dev/null
    sudo curl -fsSL -o /etc/apt/sources.list.d/ros2neuro.list https://ros2neuro.github.io/ppa/ubuntu/ros2neuro.list
    ```

    The first command installs the key that signs the packages, the second adds the repository to apt.

=== "2. Install"

    ```bash
    sudo apt update
    sudo apt install ros-jazzy-ros2neuro-full
    ```

    `ros-jazzy-ros2neuro-full` is a metapackage that installs the whole stack. A single package can be installed on its own,
    for example `sudo apt install ros-jazzy-ros2neuro-filters`: its dependencies (including the other ROS2neuro packages and
    system libraries such as Qt5, `librtfilter`, `liblsl`, `libneurodraw2`) are installed with it.

=== "3. rosdep keys (optional)"

    To let `rosdep` resolve the ROS2neuro packages when you build your own packages that depend on them:

    ```bash
    echo "yaml https://ros2neuro.github.io/ppa/ubuntu/rosdep-ros2neuro-packages.yaml" | sudo tee /etc/ros/rosdep/sources.list.d/20-ros2neuro.list
    rosdep update
    ```

## Package names

The apt name of a package is its ROS name with `ros-jazzy-` in front and the underscores replaced by dashes:

| Package | apt name |
|---|---|
| [`ros2neuro_filters`](../packages/filters/index.md) | `ros-jazzy-ros2neuro-filters` |
| [`ros2neuro_acquisition_xdf`](../packages/acquisition/xdf.md) | `ros-jazzy-ros2neuro-acquisition-xdf` |
| [`ros2neuro_decoder_sklearn`](../packages/decoder/sklearn.md) | `ros-jazzy-ros2neuro-decoder-sklearn` |
| [`ros2neuro_decoder_braindecode`](../packages/decoder/braindecode.md) | `ros-jazzy-ros2neuro-decoder-braindecode` |
| [`neurodraw`](../packages/feedback/neurodraw.md) | `libneurodraw2`, and `libneurodraw-dev` to compile against it |

## What is not in the metapackage

- **The SDK of the amplifiers**: [`ros2neuro_acquisition_antneuro`](../packages/acquisition/antneuro.md) (ANT Neuro eego) and
  [`ros2neuro_acquisition_gusbamp`](../packages/acquisition/gusbamp.md) (g.tec g.USBamp) are in the metapackage, but the manufacturer's SDK is not
  (it cannot be redistributed): install it on the computer that has the amplifier. Without it the plugins load and opening the amplifier fails with a clear message.
- **Python libraries of the Python-based decoders**: [`ros2neuro_decoder_braindecode`](../packages/decoder/braindecode.md) and
  [`ros2neuro_decoder_sklearn`](../packages/decoder/sklearn.md) are installed, but their Python libraries are not in apt: see the next section.

## Python libraries for the scikit-learn and braindecode decoders (optional)

**Required: nothing more than the packages above.** The whole stack (acquisition, filters, spectral processing, the LDA / QDA / SVM /
Gaussian decoders, integrators, control, manager, feedback, recorder, visualizer, the hardware-free launchers) runs with what apt installs.

**Optional: only to use a model made in Python.** Two decoder plugins run their model in Python, inside the decoder node, and need
libraries that are not Debian packages (or not in the version the models need):

| To use | You need (pip) | Its list |
|---|---|---|
| [`ros2neuro_decoder_sklearn`](../packages/decoder/sklearn.md) (scikit-learn models, `.skops`) | `scikit-learn` (the version the model was saved with: the examples use 1.9.0), `skops` | `/opt/ros/jazzy/share/ros2neuro_decoder_sklearn/requirements.txt` |
| [`ros2neuro_decoder_braindecode`](../packages/decoder/braindecode.md) (braindecode / PyTorch models) | `torch` (CPU or CUDA), `braindecode` | `/opt/ros/jazzy/share/ros2neuro_decoder_braindecode/requirements.txt` |

The plugins use the **system Python** (it runs inside the C++ decoder node): the libraries must be visible to it. Activating a virtual
environment is not enough. Two ways work:

```bash
# A) in your user folder (~/.local): the simplest. --break-system-packages is needed on Ubuntu 24.04 (PEP 668); with --user it
#    only writes in your home, the system is not touched.
pip install --user --break-system-packages -r /opt/ros/jazzy/share/ros2neuro_decoder_sklearn/requirements.txt
pip install --user --break-system-packages --extra-index-url https://download.pytorch.org/whl/cpu \
    -r /opt/ros/jazzy/share/ros2neuro_decoder_braindecode/requirements.txt      # CPU torch; drop --extra-index-url for CUDA

# B) in a virtual environment, made visible with PYTHONPATH (sudo apt install python3-venv first)
python3 -m venv ~/ros2neuro_py
~/ros2neuro_py/bin/pip install -r /opt/ros/jazzy/share/ros2neuro_decoder_sklearn/requirements.txt
export PYTHONPATH=~/ros2neuro_py/lib/python3.12/site-packages:$PYTHONPATH     # in every terminal that launches the decoder
```

Check: `python3 -c "import sklearn, skops, torch, braindecode"`. Without them the two plugins stop at start with an error that names the
missing module (exit code 1); the rest of the stack is not affected. The requirements pin `numpy` 2.x: it shadows the system one, which some
ROS Python packages compiled against numpy 1.x (e.g. `cv_bridge`) do not like; ros2neuro is not affected. The **Docker image** of the
installation has all of them already (torch CPU).

## Check that it works

No hardware is needed:

```bash
source /opt/ros/jazzy/setup.bash
ros2 pkg list | grep ros2neuro
ros2 launch ros2neuro_acquisition_dummy dummy_acquisition.launch.py
```

The launch file prints that the device has started and starts publishing
[`NeuroFrame`](../concepts/messages.md) messages on `/acquisition/neurodata`. For the whole chain up to the feedback, follow
[Run the complete pipeline without hardware](../tutorials/hardware-free-pipeline/index.md). With the apt installation the
launchers of [`ros2neuro_devel_test`](../reproducibility/packages/index.md) are installed with the other packages and `ros2 launch
ros2neuro_devel_test ...` finds them.

