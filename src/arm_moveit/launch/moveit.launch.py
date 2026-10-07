import os
from launch import LaunchDescription
from moveit_configs_utils import MoveItConfigsBuilder
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PythonExpression
from ament_index_python.packages import get_package_share_directory


def generate_launch_description():

    is_sim = LaunchConfiguration('is_sim')
    
    is_sim_arg = DeclareLaunchArgument(
        'is_sim',
        default_value='True'
    )

    moveit_config = (
        MoveItConfigsBuilder("arm", package_name="arm_moveit")
        .robot_description(file_path=os.path.join(
            get_package_share_directory("arm_description"),
            "urdf",
            "arm.urdf.xacro"
            ), mappings={"is_sim": is_sim}
        )
        .robot_description_semantic(file_path="config/arm.srdf")
        .trajectory_execution(file_path="config/moveit_controllers.yaml")
        .to_moveit_configs()
    )

    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[moveit_config.to_dict(), 
                    {'use_sim_time': ParameterValue(is_sim, value_type=bool)},
                    {'publish_robot_description_semantic': True}],
        arguments=["--ros-args", "--log-level", "info"],
    )

    # RViz
    config_dir = os.path.join(get_package_share_directory("arm_moveit"), "config")
    rviz_config = PythonExpression([
        "'", os.path.join(config_dir, 'moveit_vm.rviz'), "' if '", is_sim,
        "'.lower() == 'true' else '", os.path.join(config_dir, 'moveit.rviz'), "'"])
    rviz_node = Node(
        package="rviz2",
        condition=IfCondition(LaunchConfiguration("use_rviz")),
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config],
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
            moveit_config.joint_limits,
            {"use_sim_time": ParameterValue(is_sim, value_type=bool)},
        ],
    )

    return LaunchDescription(
        [
            is_sim_arg,
            DeclareLaunchArgument("use_rviz", default_value="true"),
            move_group_node, 
            rviz_node
        ]
    )