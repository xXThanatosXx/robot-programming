import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    SetEnvironmentVariable,
    AppendEnvironmentVariable
)
from launch.substitutions import Command, LaunchConfiguration
from launch.launch_description_sources import PythonLaunchDescriptionSource

from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():

    # Paquetes
    arm_description = get_package_share_directory('arm_description')
    ros_gz_sim = get_package_share_directory('ros_gz_sim')

    # Argumento para seleccionar el URDF/Xacro
    model_arg = DeclareLaunchArgument(
        name='model',
        default_value=os.path.join(
            arm_description,
            'urdf',
            'arm.urdf.xacro'
        ),
        description='Absolute path to robot URDF/Xacro file'
    )

    # Ruta para que Gazebo encuentre modelos y recursos
    gz_resource_path = AppendEnvironmentVariable(
        'GZ_SIM_RESOURCE_PATH',
        os.path.dirname(arm_description)
    )

    # Generar robot_description desde Xacro
    robot_description = ParameterValue(
        Command([
            'xacro ',
            LaunchConfiguration('model')
        ]),
        value_type=str
    )

    # Publicar TF y descripción del robot
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[
            {
                'robot_description': robot_description,
                'use_sim_time': True
            }
        ],
        output='screen'
    )

    # Iniciar Gazebo Harmonic
    start_gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                ros_gz_sim,
                'launch',
                'gz_sim.launch.py'
            )
        ),
        launch_arguments={
            'gz_args': [LaunchConfiguration('gz_args'),
                        ' --render-engine ', LaunchConfiguration('render_engine'),
                        ' --gui-config ', LaunchConfiguration('gui_config')]
        }.items()
    )

    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
        output='screen'
    )

    # Insertar robot en Gazebo
    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', 'arm',
            '-topic', 'robot_description'
        ],
        output='screen'
    )

    return LaunchDescription([
        model_arg,
        DeclareLaunchArgument(
            'gz_args', default_value=['-r ', os.path.join(get_package_share_directory('arm_description'), 'worlds', 'arm_fast.sdf')],
            description='Gazebo arguments; use -r -s empty.sdf for headless mode'
        ),
        DeclareLaunchArgument('render_engine', default_value='ogre',
                              description='Rendering engine: ogre for VMware, ogre2 for a GPU'),
        DeclareLaunchArgument('gui_config', default_value=os.path.join(
            arm_description, 'config', 'gazebo_vm.config')),
        SetEnvironmentVariable('QT_QPA_PLATFORM', 'xcb'),
        gz_resource_path,
        robot_state_publisher_node,
        start_gazebo,
        spawn_robot,
        clock_bridge
    ])
