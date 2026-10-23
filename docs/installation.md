# Installation

There are three ways to get ROS2neuro: install the Debian packages from the ROS2neuro apt repository (the quickest, no compiler
needed), use a **container** (Docker, Podman or Distrobox) with everything already installed, or build the sources in a colcon
workspace (needed to modify the code, or to use the plugins that depend on a proprietary SDK).

!!! note "Tested platform"
    Everything was built and tested on **ROS 2 Jazzy** with **Ubuntu 24.04 (noble)**, and the Debian packages
    (`ros-jazzy-ros2neuro-*`) are built for that combination. Other releases have not been tested: on them use the container below or build from source
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

## Use a container (Docker, Podman, Distrobox)

If you are not on Ubuntu 24.04, or you just want to try ROS2neuro without touching your system, build an image with Ubuntu 24.04,
ROS 2 Jazzy and ROS2neuro already installed from the apt repository. The
[`Dockerfile`](https://github.com/ros2neuro/ppa/blob/main/docker/Dockerfile) is in the
[`ppa`](https://github.com/ros2neuro/ppa) repository. It works with Docker and with Podman (replace `docker` with `podman`);
amd64 only.

```bash
git clone https://github.com/ros2neuro/ppa.git
docker build -t ros2neuro ppa/docker/
```

=== "Docker / Podman"

    Run the dummy acquisition (no hardware, no window) and look at its data from a second terminal:

    ```bash
    docker run -it --rm --name ros2neuro ros2neuro ros2 launch ros2neuro_acquisition_dummy dummy_acquisition.launch.py

    # second terminal
    docker exec -it ros2neuro bash -c 'source /opt/ros/jazzy/setup.bash && ros2 topic hz /acquisition/neurodata'   # ~16 Hz
    ```

    Run the whole chain on a recorded GDF and open the feedback window (the wheel; use `gaussian_bars` for the bars):

    ```bash
    xhost +local:                                     # let the container open windows on your screen
    docker run -it --rm \
        -e DISPLAY=$DISPLAY -e LIBGL_ALWAYS_SOFTWARE=1 -v /tmp/.X11-unix:/tmp/.X11-unix --network host \
        ros2neuro ros2 launch ros2neuro_devel_test gaussian_wheel.launch.xml protocol:=calibration record:=false
    xhost -local:                                     # when you are done
    ```

    Notes:

    - `LIBGL_ALWAYS_SOFTWARE=1` draws with the CPU and works everywhere. With a GPU you can add `--device /dev/dri` and drop it;
      with NVIDIA and the NVIDIA Container Toolkit use `--gpus all -e NVIDIA_DRIVER_CAPABILITIES=graphics,utility`.
    - To keep the recordings, mount a folder and pass it to the launcher:
      `-v $HOME/recordings:/home/ubuntu/recordings` and `record:=true recordings_dir:=/home/ubuntu/recordings`.
    - A real amplifier needs its device inside the container (`--device /dev/ttyUSB0`, ...); an LSL stream from another machine
      needs `--network host`. If Fast DDS complains about shared memory when nodes run in different containers, add
      `--ipc=host` to all of them.

=== "Distrobox"

    [Distrobox](https://distrobox.it/) shares your screen, home folder and devices with the container, so no `xhost` or `-v`
    options are needed. Create the container from the same image: Distrobox uses Podman when it is installed (Docker
    otherwise), so build the image with the same engine.

    ```bash
    podman build -t ros2neuro_ppa ppa/docker/                                  # or: docker build ...
    distrobox create --name ros2neuro_ppa --image localhost/ros2neuro_ppa      # first start takes a minute
    distrobox enter ros2neuro_ppa

    # inside the container
    source /opt/ros/jazzy/setup.bash
    ros2 launch ros2neuro_acquisition_dummy dummy_acquisition.launch.py
    ros2 launch ros2neuro_devel_test gaussian_wheel.launch.xml protocol:=calibration record:=false
    ```

    A "problem setting up the user ... trying manual addition" message on the first start is normal with older Distrobox
    versions (tested with 1.4.1). Your home folder is shared with the host: do not `source` another ROS 2 workspace inside the
    container. Remove it with `distrobox rm -f ros2neuro_ppa`.

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
