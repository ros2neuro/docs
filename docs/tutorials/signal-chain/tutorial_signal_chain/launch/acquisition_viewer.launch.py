"""Tutorial: replay a GDF file and look at it in the visualizer.

    ros2 launch tutorial_signal_chain acquisition_viewer.launch.py
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

CONFIG = os.path.join(get_package_share_directory('tutorial_signal_chain'), 'config')
# the GDF that comes with ros2neuro_devel_test
GDF = os.path.join(get_package_share_directory('ros2neuro_devel_test'), 'data', 'test.gdf')


def generate_launch_description():
    # --8<-- [start:acquisition]
    acquisition = Node(
        package='ros2neuro_acquisition', executable='acquisition', name='acquisition', output='screen',
        parameters=[os.path.join(CONFIG, 'acquisition_gdf.yaml'),
                    {'acquisition.filename': LaunchConfiguration('gdf_file')}])
    # --8<-- [end:acquisition]

    # --8<-- [start:viewer]
    viewer = Node(package='ros2neuro_visualizer', executable='neuroviz', name='neuroviz', output='screen')
    # --8<-- [end:viewer]

    return LaunchDescription([
        DeclareLaunchArgument('gdf_file', default_value=GDF, description='GDF file to replay'),
        acquisition,
        viewer,
    ])
