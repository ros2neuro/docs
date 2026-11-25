"""Tutorial: replay a GDF file, look at it in the visualizer and record it again.

    ros2 launch tutorial_signal_chain acquisition_recorder.launch.py output:=/tmp/recordings subject:=sub-01
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

    viewer = Node(package='ros2neuro_visualizer', executable='neuroviz', name='neuroviz', output='screen')

    # --8<-- [start:recorder]
    recorder = Node(
        package='ros2neuro_recorder', executable='recorder', name='recorder', output='screen',
        parameters=[{
            'plugin': 'ros2neuro::recorder::XDFRecorder',
            'topic_data': '/acquisition/neurodata',          # where the acquisition publishes
            'topic_info': '/acquisition/neurodata_info',
            'topic_event': '/neuroevent',
            'output': LaunchConfiguration('output'),         # folder of the file
            'subject': LaunchConfiguration('subject'),
            'task': 'tutorial',
            'xdf.file_type': 'gdf',
        }])
    # --8<-- [end:recorder]

    return LaunchDescription([
        DeclareLaunchArgument('gdf_file', default_value=GDF, description='GDF file to replay'),
        DeclareLaunchArgument('output', default_value='/tmp/recordings', description='folder of the recording'),
        DeclareLaunchArgument('subject', default_value='sub-01'),
        acquisition,
        viewer,
        recorder,
    ])
