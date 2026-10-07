import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('enable_alexa', default_value='false'),
        DeclareLaunchArgument('port', default_value='/dev/ttyACM0'),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory('arm_controller'), 'launch', 'controller.launch.py')),
            launch_arguments={'is_sim': 'false', 'port': LaunchConfiguration('port')}.items()),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory('arm_moveit'), 'launch', 'moveit.launch.py')),
            launch_arguments={'is_sim': 'false'}.items()),
        IncludeLaunchDescription(PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory('arm_remote'), 'launch', 'remote_interface.launch.py')),
            launch_arguments={'is_sim': 'false', 'enable_alexa': LaunchConfiguration('enable_alexa')}.items()),
    ])
