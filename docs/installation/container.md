# Use a container (Docker, Podman, Distrobox)

Ubuntu 24.04 with ROS 2 Jazzy and ROS2neuro inside an image, whatever your system.



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

    Run the whole chain on a recorded GDF and open the feedback window (the wheel; use `test_feedback_bars2` for the bars):

    ```bash
    xhost +local:                                     # let the container open windows on your screen
    docker run -it --rm \
        -e DISPLAY=$DISPLAY -e LIBGL_ALWAYS_SOFTWARE=1 -v /tmp/.X11-unix:/tmp/.X11-unix --network host \
        ros2neuro ros2 launch ros2neuro_devel_test feedback_wheel.launch.py
    xhost -local:                                     # when you are done
    ```

    Notes:

    - `LIBGL_ALWAYS_SOFTWARE=1` draws with the CPU and works everywhere. With a GPU you can add `--device /dev/dri` and drop it;
      with NVIDIA and the NVIDIA Container Toolkit use `--gpus all -e NVIDIA_DRIVER_CAPABILITIES=graphics,utility`.
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
    ros2 launch ros2neuro_devel_test feedback_wheel.launch.py
    ```

    A "problem setting up the user ... trying manual addition" message on the first start is normal with older Distrobox
    versions (tested with 1.4.1). Your home folder is shared with the host: do not `source` another ROS 2 workspace inside the
    container. Remove it with `distrobox rm -f ros2neuro_ppa`.

