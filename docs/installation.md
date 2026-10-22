# Installation

There are two ways to get ROS2neuro: install the Debian packages from the ROS2neuro apt repository (the quickest, no compiler
needed), or build the sources in a colcon workspace (needed to modify the code, or to use the plugins that depend on a
proprietary SDK).

!!! note "Tested platform"
    Everything was built and tested on **ROS 2 Jazzy** with **Ubuntu 24.04 (noble)**, and the Debian packages
    (`ros-jazzy-ros2neuro-*`) are built for that combination. Other releases have not been tested: on them, build from source
    at your own risk.

## Install from the apt repository

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

### Package names

The apt name of a package is its ROS name with `ros-jazzy-` in front and the underscores replaced by dashes:

| Package | apt name |
|---|---|
| [`ros2neuro_filters`](packages/filters/index.md) | `ros-jazzy-ros2neuro-filters` |
| [`ros2neuro_acquisition_xdf`](packages/acquisition/xdf.md) | `ros-jazzy-ros2neuro-acquisition-xdf` |
| [`ros2neuro_decoder_py`](packages/decoder/python.md) | `ros-jazzy-ros2neuro-decoder-py` |
| [`neurodraw`](packages/feedback/neurodraw.md) | `libneurodraw2`, and `libneurodraw-dev` to compile against it |

### What is not in the metapackage

- **Plugins with a proprietary SDK**: [`ros2neuro_acquisition_antneuro`](packages/acquisition/antneuro.md) (ANT Neuro eego SDK) and
  [`ros2neuro_acquisition_gusbamp`](packages/acquisition/gusbamp.md) (g.tec g.USBamp API) are not packaged: build them from source
  on a machine that has the SDK.
- **Python deep-learning libraries**: [`ros2neuro_decoder_py`](packages/decoder/python.md) is installed, but `torch` and
  `braindecode` are not in apt. Install them with `pip` (preferably in a virtual environment) before using a deep-learning model.

### Check that it works

No hardware is needed:

```bash
source /opt/ros/jazzy/setup.bash
ros2 pkg list | grep ros2neuro
ros2 launch ros2neuro_acquisition_dummy dummy_acquisition.launch.py
```

The launch file prints that the device has started and starts publishing
[`NeuroFrame`](concepts/messages.md) messages on `/acquisition/neurodata`. For the whole chain up to the feedback, follow
[Running the whole pipeline without hardware](tutorials/hardware-free-pipeline/index.md). With the apt installation the
launchers of [`ros2neuro_devel_test`](packages/devel-test.md) are installed with the other packages and `ros2 launch
ros2neuro_devel_test ...` finds them.

## Build from source

Use this to change the code, to develop a plugin, or for a ROS 2 or Ubuntu release without packages.

1. Install ROS 2 and the build tools (`colcon`, `rosdep`).
2. Clone the repositories of the [ros2neuro organization](https://github.com/ros2neuro) you need into the `src/` folder of a
   workspace: there is one repository per package. [`neurodraw`](packages/feedback/neurodraw.md) is plain CMake and is needed only
   by the feedback plugins.
3. Install the dependencies and build:

    ```bash
    cd <workspace>
    rosdep install --from-paths src --ignore-src -r -y
    colcon build
    source install/setup.bash
    ```

    Use `colcon build --packages-select <package>` to build one package, and `--packages-skip` for the ones whose SDK you do not
    have (for example [`ros2neuro_acquisition_gusbamp`](packages/acquisition/gusbamp.md)).

The dependencies of each package, with the system libraries it needs, are listed in the **Dependencies** section of its page.

## Mixing the two

The installed packages live in `/opt/ros/jazzy`. A workspace sourced **after** it overlays them: a package you build from source
takes precedence over the installed one with the same name, so you can install the stack from apt and rebuild only the package
you are working on.

```bash
source /opt/ros/jazzy/setup.bash
source <workspace>/install/setup.bash
```
