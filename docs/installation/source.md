# Build from source

Needed to modify the code or to develop a plugin.



Use this to change the code, to develop a plugin, or for a ROS 2 or Ubuntu release without packages.

1. Install ROS 2 and the build tools (`colcon`, `rosdep`).
2. Clone the repositories of the [ros2neuro organization](https://github.com/ros2neuro) you need into the `src/` folder of a
   workspace: there is one repository per package. [`neurodraw`](../packages/feedback/neurodraw.md) is plain CMake and is needed only
   by the feedback plugins.
3. Install the dependencies and build:

    ```bash
    cd <workspace>
    rosdep install --from-paths src --ignore-src -r -y
    colcon build
    source install/setup.bash
    ```

    Use `colcon build --packages-select <package>` to build one package, and `--packages-skip` for the ones whose SDK you do not
    have (for example [`ros2neuro_acquisition_gusbamp`](../packages/acquisition/gusbamp.md)).

The dependencies of each package, with the system libraries it needs, are listed in the **Dependencies** section of its page.
`rosdep` does not install the Python libraries of the scikit-learn and braindecode decoders: install them as in
[the section above](apt.md#python-libraries-for-the-scikit-learn-and-braindecode-decoders-optional), with the `requirements.txt` of the package
(`src/<package>/requirements.txt`).


## Mixing the two

The installed packages live in `/opt/ros/jazzy`. A workspace sourced **after** it overlays them: a package you build from source
takes precedence over the installed one with the same name, so you can install the stack from apt and rebuild only the package
you are working on.

```bash
source /opt/ros/jazzy/setup.bash
source <workspace>/install/setup.bash
```
