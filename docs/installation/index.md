# Installation

There are three ways to get ROS2neuro. Pick one: they give the same stack.

!!! note "Tested platform"
    Everything was built and tested on **ROS 2 Jazzy** with **Ubuntu 24.04 (noble)**, and the Debian packages
    (`ros-jazzy-ros2neuro-*`) are built for that combination. Other releases have not been tested: on them use the container or build from source
    at your own risk.

## What is in this menu

| Method | When to use it | Page |
|---|---|---|
| **Install from apt** | you are on Ubuntu 24.04 with ROS 2 Jazzy and just want to use ROS2neuro: no compiler, one `apt install` | [Install from the apt repository](apt.md) |
| **Use a container** | another system, or you want to try ROS2neuro without touching yours: Docker, Podman or Distrobox with everything inside | [Use a container](container.md) |
| **Build from source** | you want to change the code, write a plugin, or use a release without packages | [Build from source](source.md) |

Inside the pages:

| To... | Go to |
|---|---|
| add the repository and install the whole stack | [apt: add the repository and install](apt.md#install-the-repository-and-the-packages) |
| find the apt name of one package | [apt: package names](apt.md#package-names) |
| use the scikit-learn or braindecode decoders (optional Python libraries) | [apt: Python libraries](apt.md#python-libraries-for-the-scikit-learn-and-braindecode-decoders-optional) |
| check that it works, without hardware | [apt: check that it works](apt.md#check-that-it-works) |
| open a feedback window from a container | [container: Docker / Podman or Distrobox](container.md) |
| keep the installed stack and rebuild one package | [source: mixing the two](source.md#mixing-the-two) |

After installing, follow [Run the complete pipeline without hardware](../tutorials/hardware-free-pipeline/index.md), or start with the [Concepts](../concepts/index.md).
