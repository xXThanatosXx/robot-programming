"""Start Gazebo Harmonic and the arm controllers on ROS 2 Jazzy."""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('gz_args', default_value=['-r ', os.path.join(get_package_share_directory('arm_description'), 'worlds', 'arm_fast.sdf')]),
        DeclareLaunchArgument('render_engine', default_value='ogre'),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(
                get_package_share_directory('arm_description'),
                'launch', 'gazebo.launch.py')),
            launch_arguments={
                'gz_args': LaunchConfiguration('gz_args'),
                'render_engine': LaunchConfiguration('render_engine')}.items()),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(
                get_package_share_directory('arm_controller'),
                'launch', 'controller.launch.py')),
            launch_arguments={'is_sim': 'true'}.items()),
    ])
