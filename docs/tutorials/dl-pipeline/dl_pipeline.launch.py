"""A complete pipeline with a deep-learning model, without hardware.

    ros2 launch dl_pipeline.launch.py        (from this folder; needs ros2neuro_devel_test for the GDF)

data/test_mi.gdf (replayed as if it were live) -> Butterworth 4-14 Hz -> Buffer (512 samples) -> ShallowNet (braindecode) -> exponential
integrator -> control + manager (an evaluation of 4 trials) -> feedback window (the wheel). The session ends by itself.
"""
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import ExecuteProcess, Shutdown, TimerAction
from launch_ros.actions import Node

CFG = Path(__file__).resolve().parent / 'config'
GDF = Path(get_package_share_directory('ros2neuro_devel_test')) / 'data' / 'test_mi.gdf'
MODEL = Path(get_package_share_directory('ros2neuro_decoder_braindecode')) / 'extra' / 'eegnet_mi_bhbf' / 'manifest.yaml'
DELAY = 15.0   # seconds before the acquisition starts: every other node is up and the network is loaded
SETTLE = 8.0   # seconds more: the acquisition has found all its subscribers, and only then is started


def generate_launch_description():
    chain, layout, protocol = str(CFG / 'chain.yaml'), str(CFG / 'layout.yaml'), str(CFG / 'protocol.yaml')
    nodes = [
        Node(package='ros2neuro_filters', executable='filter_chain_node', name='filters', output='screen', parameters=[chain],
             remappings=[('/neurodata', '/acquisition/neurodata'), ('~/filtered', '/processing/filtered')]),
        Node(package='ros2neuro_processing', executable='processing_node', name='buffer', output='screen', parameters=[chain],
             remappings=[('/neurodata', '/processing/filtered'), ('/features', '/processing/buffer')]),
        Node(package='ros2neuro_decoder', executable='decoder_node', name='decoder', output='screen',
             parameters=[chain, {'decoder.manifest': str(MODEL)}],
             remappings=[('/features', '/processing/buffer'), ('~/prediction', '/classification/prediction')]),
        Node(package='ros2neuro_integrator', executable='integrator_node', name='integrator', output='screen', parameters=[str(CFG / 'integrator.yaml')]),
        Node(package='ros2neuro_feedback', executable='feedback_node', name='feedback', output='screen', parameters=[layout, str(CFG / 'feedback.yaml')]),
    ]
    # the acquisition starts SWITCHED OFF and is started with a service call, together with control and manager: all the nodes get the first frame
    acquisition = Node(package='ros2neuro_acquisition', executable='acquisition', name='acquisition', output='screen',
                       parameters=[str(CFG / 'acquisition.yaml'), {'acquisition.filename': str(GDF), 'acquisition.autostart': False}])
    start = ExecuteProcess(cmd=['ros2', 'service', 'call', '/acquisition/start', 'std_srvs/srv/Empty', '{}'], output='screen')
    session = [
        Node(package='ros2neuro_control', executable='control_node', name='control', output='screen', on_exit=Shutdown(), parameters=[layout, protocol]),
        Node(package='ros2neuro_manager', executable='manager_node', name='manager', output='screen', on_exit=Shutdown(), parameters=[layout, protocol]),
    ]
    return LaunchDescription(nodes + [TimerAction(period=DELAY, actions=[acquisition]), TimerAction(period=DELAY + SETTLE, actions=[start] + session)])
