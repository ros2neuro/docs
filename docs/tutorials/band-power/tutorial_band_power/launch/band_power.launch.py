"""Tutorial: acquisition -> alpha band-pass (8-13 Hz) -> band power -> /bandpower.

    ros2 launch tutorial_band_power band_power.launch.py
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

CONFIG = os.path.join(get_package_share_directory('tutorial_band_power'), 'config')
GDF = os.path.join(get_package_share_directory('ros2neuro_devel_test'), 'data', 'test.gdf')


def generate_launch_description():
    # --8<-- [start:nodes]
    alpha = Node(                                                    # 1. the band-pass: publishes /alpha/filtered
        package='ros2neuro_filters', executable='filter_chain_node', name='alpha', output='screen',
        parameters=[os.path.join(CONFIG, 'alpha_chain.yaml')],
        remappings=[('/neurodata', '/acquisition/neurodata')])

    band_power = Node(                                               # 2. the power of that band: publishes /bandpower
        package='tutorial_band_power', executable='band_power_node', name='band_power', output='screen',
        parameters=[os.path.join(CONFIG, 'band_power.yaml')],
        remappings=[('/neurodata', '/alpha/filtered')])
    # --8<-- [end:nodes]

    acquisition = Node(
        package='ros2neuro_acquisition', executable='acquisition', name='acquisition', output='screen',
        parameters=[os.path.join(CONFIG, 'acquisition_gdf.yaml'),
                    {'acquisition.filename': LaunchConfiguration('gdf_file')}])

    viewer = Node(package='ros2neuro_visualizer', executable='neuroviz', name='neuroviz', output='screen')

    return LaunchDescription([
        DeclareLaunchArgument('gdf_file', default_value=GDF, description='GDF file to replay'),
        alpha, band_power, viewer,
        TimerAction(period=3.0, actions=[acquisition]),     # the source starts 3 s later, so nobody loses the first frames
    ])
