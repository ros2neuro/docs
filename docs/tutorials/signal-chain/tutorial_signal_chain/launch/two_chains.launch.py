"""Tutorial: acquisition -> two filter chains in parallel (mu and beta) -> visualizer.

    ros2 launch tutorial_signal_chain two_chains.launch.py
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

CONFIG = os.path.join(get_package_share_directory('tutorial_signal_chain'), 'config')
GDF = os.path.join(get_package_share_directory('ros2neuro_devel_test'), 'data', 'test.gdf')


def generate_launch_description():
    acquisition = Node(
        package='ros2neuro_acquisition', executable='acquisition', name='acquisition', output='screen',
        parameters=[os.path.join(CONFIG, 'acquisition_gdf.yaml'),
                    {'acquisition.filename': LaunchConfiguration('gdf_file')}])

    # --8<-- [start:chains]
    def band_chain(name):
        """The same executable, started twice: the name picks the YAML section and the output topic."""
        return Node(
            package='ros2neuro_filters', executable='filter_chain_node', name=name, output='screen',
            parameters=[os.path.join(CONFIG, 'two_chains.yaml')],
            remappings=[('/neurodata', '/acquisition/neurodata')])   # both read the same raw signal

    mu = band_chain('mu')        # publishes /mu/filtered
    beta = band_chain('beta')    # publishes /beta/filtered
    # --8<-- [end:chains]

    viewer = Node(package='ros2neuro_visualizer', executable='neuroviz', name='neuroviz', output='screen')

    return LaunchDescription([
        DeclareLaunchArgument('gdf_file', default_value=GDF, description='GDF file to replay'),
        acquisition,
        mu,
        beta,
        viewer,
    ])
