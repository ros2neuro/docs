# Python decoder (deep learning)

!!! info ""
    Package: [`ros2neuro_decoder_py`](https://github.com/ros2neuro/ros2neuro_decoder_py) · part of [Decoder](index.md)

Python implementation of the EEG decoder for ROS2Neuro.

This package allows the integration of machine learning and deep learning algorithms (using libraries such as `braindecode`, `skops`, `torch`, etc.) for EEG decoding directly into the ROS2Neuro framework.

## Setup Instructions

It is highly recommended to use a Python virtual environment to manage dependencies when building and running this package alongside ROS 2.

### 1. Create and Activate a Virtual Environment

Navigate to the root of your `ros2neuro` workspace and create a virtual environment (if you haven't already):

```bash
cd ~/neurorobotics/ros2neuro_ws
python3 -m venv ros2neuro_venv
```

Activate the virtual environment:

```bash
source ros2neuro_venv/bin/activate
```

*(Note: You will need to activate this virtual environment every time you want to build or run this package in a new terminal).*

### 2. Install Python Dependencies

With the virtual environment activated, install the necessary Python dependencies for this package:

```bash
cd ~/neurorobotics/ros2neuro_ws/src/ros2neuro_decoder_py
pip install -r requirements.txt
```

### 3. Build the Package

Ensure your ROS 2 installation is sourced (e.g., `source /opt/ros/humble/setup.bash`), and your virtual environment is active. Then, build the package using `colcon` from the root of the workspace:

```bash
cd ~/neurorobotics/ros2neuro_ws
colcon build --packages-select ros2neuro_decoder_py
```

### 4. Running the Package (Example)

After a successful build, source the workspace installation map alongside the virtual environment to run the nodes:

```bash
cd ~/neurorobotics/ros2neuro_ws
source install/setup.bash
source ros2neuro_venv/bin/activate

ros2 launch ros2neuro_decoder_py example_decoder.launch.xml
```
