from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from moveit_configs_utils import MoveItConfigsBuilder
from ament_index_python.packages import get_package_share_directory
import os


def generate_launch_description():
    is_sim = LaunchConfiguration('is_sim')
    config = (MoveItConfigsBuilder('arm', package_name='arm_moveit')
              .robot_description(file_path=os.path.join(
                  get_package_share_directory('arm_description'), 'urdf', 'arm.urdf.xacro'),
                  mappings={'is_sim': is_sim})
              .robot_description_semantic(file_path='config/arm.srdf')
              .to_moveit_configs())
    return LaunchDescription([
        DeclareLaunchArgument('is_sim', default_value='true'),
        DeclareLaunchArgument('enable_alexa', default_value='false'),
        Node(package='arm_remote', executable='task_server_node',
             parameters=[config.to_dict(),
                         {'use_sim_time': ParameterValue(is_sim, value_type=bool)}],
             output='screen'),
        Node(package='arm_remote', executable='alexa_interface.py',
             condition=IfCondition(LaunchConfiguration('enable_alexa')),
             output='screen'),
    ])
