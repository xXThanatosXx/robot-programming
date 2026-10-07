import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('enable_alexa', default_value='false'),
        DeclareLaunchArgument('use_rviz', default_value='true'),
        DeclareLaunchArgument('gz_args', default_value=['-r ', os.path.join(get_package_share_directory('arm_description'), 'worlds', 'arm_fast.sdf')]),
        DeclareLaunchArgument('render_engine', default_value='ogre'),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory('arm_controller'), 'launch', 'simulation.launch.py')),
            launch_arguments={'gz_args': LaunchConfiguration('gz_args'), 'render_engine': LaunchConfiguration('render_engine')}.items()),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory('arm_moveit'), 'launch', 'moveit.launch.py')),
            launch_arguments={'is_sim': 'true', 'use_rviz': LaunchConfiguration('use_rviz')}.items()),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory('arm_remote'), 'launch', 'remote_interface.launch.py')),
            launch_arguments={'is_sim': 'true', 'enable_alexa': LaunchConfiguration('enable_alexa')}.items()),
    ])
