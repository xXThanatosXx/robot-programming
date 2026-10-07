import os
from ament_index_python.packages import get_package_share_directory
from launch.conditions import UnlessCondition
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch.substitutions import Command, LaunchConfiguration


def generate_launch_description():

    is_sim = LaunchConfiguration('is_sim')
    description = ParameterValue(Command([
        'xacro ', os.path.join(get_package_share_directory('arm_description'),
                              'urdf', 'arm.urdf.xacro'),
        ' is_sim:=false port:=', LaunchConfiguration('port')]), value_type=str)
    publisher = Node(package='robot_state_publisher', executable='robot_state_publisher',
                     parameters=[{'robot_description': description}],
                     condition=UnlessCondition(is_sim))
    manager = Node(package='controller_manager', executable='ros2_control_node',
                   parameters=[os.path.join(get_package_share_directory('arm_controller'),
                                            'config', 'arm_controllers.yaml'),
                               {'use_sim_time': False}],
                   remappings=[('robot_description', '/robot_description')],
                   condition=UnlessCondition(is_sim))

    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        parameters=[{"use_sim_time": ParameterValue(LaunchConfiguration("is_sim"), value_type=bool)}],
        arguments=[
            "joint_state_broadcaster",
            "--controller-manager",
            "/controller_manager",
        ],
    )

    arm_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        parameters=[{"use_sim_time": ParameterValue(LaunchConfiguration("is_sim"), value_type=bool)}],
        arguments=["arm_controller", "--controller-manager", "/controller_manager"],
    )

    gripper_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        parameters=[{"use_sim_time": ParameterValue(LaunchConfiguration("is_sim"), value_type=bool)}],
        arguments=["gripper_controller", "--controller-manager", "/controller_manager"],
    )

    return LaunchDescription(
        [
            DeclareLaunchArgument("is_sim", default_value="true"),
            DeclareLaunchArgument("port", default_value="/dev/ttyACM0"),
            publisher,
            manager,
            joint_state_broadcaster_spawner,
            arm_controller_spawner,
            gripper_controller_spawner,
        ]
    )
