"""Tutorial: the whole pipeline, from the GDF replay to the integrated probabilities.

    ros2 launch tutorial_signal_chain pipeline.launch.py
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, TimerAction
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

CONFIG = os.path.join(get_package_share_directory('tutorial_signal_chain'), 'config')
DEVEL = get_package_share_directory('ros2neuro_devel_test')
GDF = os.path.join(DEVEL, 'data', 'test.gdf')
MODEL = os.path.join(DEVEL, 'data', 'models', 'gaussian', 'manifest.yaml')
PIPELINE = os.path.join(CONFIG, 'pipeline.yaml')


def generate_launch_description():
    # --8<-- [start:acquisition]
    acquisition = Node(
        package='ros2neuro_acquisition', executable='acquisition', name='acquisition', output='screen',
        parameters=[os.path.join(CONFIG, 'acquisition_gdf.yaml'),
                    {'acquisition.filename': LaunchConfiguration('gdf_file')}])
    # --8<-- [end:acquisition]

    # --8<-- [start:filters]
    filters = Node(
        package='ros2neuro_filters', executable='filter_chain_node', name='filters', output='screen',
        parameters=[PIPELINE],
        remappings=[('/neurodata', '/acquisition/neurodata'),
                    ('~/filtered', '/processing/filtered')])
    # --8<-- [end:filters]

    # --8<-- [start:welch]
    welch = Node(
        package='ros2neuro_processing', executable='processing_node', name='welch', output='screen',
        parameters=[PIPELINE],
        remappings=[('/neurodata', '/processing/filtered'),
                    ('/features', '/processing/psd')])
    # --8<-- [end:welch]

    # --8<-- [start:decoder]
    decoder = Node(
        package='ros2neuro_decoder', executable='decoder_node', name='decoder', output='screen',
        parameters=[{'decoder.manifest': MODEL}],
        remappings=[('/features', '/processing/psd'),
                    ('~/prediction', '/classification/prediction')])
    # --8<-- [end:decoder]

    # --8<-- [start:integrator]
    integrator = Node(
        package='ros2neuro_integrator', executable='integrator_node', name='integrator', output='screen',
        parameters=[PIPELINE])
    # --8<-- [end:integrator]

    viewer = Node(package='ros2neuro_visualizer', executable='neuroviz', name='neuroviz', output='screen')

    # --8<-- [start:description]
    return LaunchDescription([
        DeclareLaunchArgument('gdf_file', default_value=GDF, description='GDF file to replay'),
        filters, welch, decoder, integrator, viewer,      # the listeners start at once...
        TimerAction(period=3.0, actions=[acquisition]),   # ...and the source 3 seconds later, so nobody misses the first frame
    ])
    # --8<-- [end:description]
