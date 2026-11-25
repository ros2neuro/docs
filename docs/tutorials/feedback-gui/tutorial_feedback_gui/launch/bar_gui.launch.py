"""Tutorial: the band power of the alpha band (tutorial_band_power) and a bar that follows one channel.

    ros2 launch tutorial_feedback_gui bar_gui.launch.py channel:=9
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    # --8<-- [start:include]
    # 1. everything we already built: acquisition -> alpha band-pass -> band power (-> /bandpower)
    band_power = IncludeLaunchDescription(PythonLaunchDescriptionSource(
        os.path.join(get_package_share_directory('tutorial_band_power'), 'launch', 'band_power.launch.py')))
    # --8<-- [end:include]

    # --8<-- [start:gui]
    # 2. the window; `channel` is a launch argument, so it can be given on the command line
    gui = Node(package='tutorial_feedback_gui', executable='bar_gui.py', name='bar_gui', output='screen',
               parameters=[{'channel': LaunchConfiguration('channel')}])
    # --8<-- [end:gui]

    return LaunchDescription([
        DeclareLaunchArgument('channel', default_value='1', description='channel to show (1 is the first)'),
        band_power,
        gui,
    ])
