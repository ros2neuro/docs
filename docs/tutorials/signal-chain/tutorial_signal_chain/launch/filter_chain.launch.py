"""Tutorial: acquisition -> filter chain -> visualizer.

    ros2 launch tutorial_signal_chain filter_chain.launch.py
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

    # --8<-- [start:chain]
    chain = Node(
        package='ros2neuro_filters', executable='filter_chain_node',
        name='filter_chain',                                    # the section of the YAML file
        output='screen',
        parameters=[os.path.join(CONFIG, 'filter_chain.yaml')],
        remappings=[('/neurodata', '/acquisition/neurodata')])  # read the acquisition; it writes /filter_chain/filtered
    # --8<-- [end:chain]

    viewer = Node(package='ros2neuro_visualizer', executable='neuroviz', name='neuroviz', output='screen')

    return LaunchDescription([
        DeclareLaunchArgument('gdf_file', default_value=GDF, description='GDF file to replay'),
        acquisition,
        chain,
        viewer,
    ])
