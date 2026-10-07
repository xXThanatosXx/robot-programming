# Brazo robótico — ROS 2 Jazzy

Proyecto para Ubuntu 24.04, ROS 2 Jazzy y Gazebo Harmonic.
La simulación utiliza `ros_gz_sim`, `ros_gz_bridge` y `gz_ros2_control`.

## Dependencias y compilación

En una terminal nueva, sin cargar un workspace Humble:

```bash
cd ~/robot-programming
source /opt/ros/jazzy/setup.bash
# Solo si rosdep todavía no está inicializado:
sudo rosdep init
rosdep update
rosdep install --from-paths src --ignore-src --rosdistro jazzy -y
colcon build --symlink-install --build-base build_jazzy --install-base install_jazzy
source install_jazzy/setup.bash
```

Los directorios `build_jazzy` e `install_jazzy` separan los artefactos nuevos de los anteriores.

## Ejecutar

Simulación y los tres controladores:

```bash
ros2 launch arm_controller simulation.launch.py
```

Sin interfaz gráfica:

```bash
ros2 launch arm_controller simulation.launch.py gz_args:="-r -s $(ros2 pkg prefix --share arm_description)/worlds/arm_fast.sdf"
```

En otras terminales, cargar `/opt/ros/jazzy/setup.bash` e `install_jazzy/setup.bash`:

```bash
# Control con deslizadores; iniciar primero arm_description gazebo.launch.py.
ros2 launch arm_controller slider_controller.launch.py
# Planificación MoveIt y RViz; requiere la simulación anterior.
ros2 launch arm_moveit moveit.launch.py is_sim:=true
# Visualización del modelo sin Gazebo:
ros2 launch arm_description display.launch.py
```

`slider_controller.launch.py` inicia los spawners. Para usarlo, iniciar solo
`ros2 launch arm_description gazebo.launch.py` en la primera terminal,
o ejecutar el nodo y GUI por separado si los controladores ya están activos.

Verificar los controladores:

```bash
ros2 control list_controllers
```

Deben aparecer `joint_state_broadcaster`, `arm_controller` y
`gripper_controller` en estado `active`. `joint_5` sigue a `joint_4` mediante
el atributo URDF `mimic`; no recibe comandos independientes.

La configuración admite simulación y un brazo físico mediante el plugin serie
`arm_controller/armInterface`. El estado físico es estimado desde los comandos;
el firmware original no transmite posiciones medidas.

Referencia: https://control.ros.org/jazzy/doc/gz_ros2_control/doc/index.html

## Instalación de ros2_control con versiones mezcladas

Si Gazebo informa `libpal_statistics.so` ausente o `undefined symbol` al cargar
`gz_ros2_control`, actualizar también las bibliotecas concretas (actualizar
solo el metapaquete `ros2-control` no garantiza actualizar las dependencias):

```bash
sudo apt update
sudo apt install ros-jazzy-pal-statistics ros-jazzy-hardware-interface \
  ros-jazzy-controller-manager ros-jazzy-controller-interface \
  ros-jazzy-control-toolbox ros-jazzy-joint-trajectory-controller \
  ros-jazzy-joint-state-broadcaster ros-jazzy-ros2controlcli
```

## Gráficos en VMware

El lanzamiento usa Ogre y una ventana de 960 × 640 con menos paneles.
Para probar Ogre2 en un equipo con aceleración gráfica:

```bash
ros2 launch arm_controller simulation.launch.py render_engine:=ogre2
```

Si aún parpadea, probar renderizado por software (puede consumir más CPU):

```bash
LIBGL_ALWAYS_SOFTWARE=1 ros2 launch arm_controller simulation.launch.py
```

La aceleración 3D y memoria gráfica de VMware se ajustan desde el anfitrión
con la máquina virtual apagada.

## Proyecto completo migrado desde Humble

Fuente: rama `Robot-Arm-Real-Robot` de
https://github.com/xXThanatosXx/RoboticaIndustrial, commit
`b56023e15a0b34799ec461261acb91d5dafbb1bf`.

Iniciar Gazebo, controladores, MoveIt, RViz y servidor de tareas juntos:

```bash
source /opt/ros/jazzy/setup.bash
source ~/robot-programming/install_jazzy/setup.bash
ros2 launch arm_bringup simulated_robot.launch.py
```

Enviar una tarea desde otra terminal con el mismo entorno:

```bash
ros2 action send_goal /task_server arm_msgs/action/ArmTask '{task_number: 0}' --feedback
```

Tareas originales: `0` inicio (pinza abierta), `1` recoger, `2` reposo.
Las tareas inválidas o simultáneas se rechazan; los fallos de planificación o
movimiento devuelven un resultado fallido. La cancelación solicita detener
los grupos de MoveIt.

### Robot real

Cargar `src/arm_firmware/firmware/robot_control/robot_control.ino` en Arduino.
Pines de servos: base 8, hombro 9, codo 10, pinza 11; serie 115200 baudios.
Conectar USB al sistema invitado VMware y seleccionar el puerto real:

```bash
ros2 launch arm_bringup real_robot.launch.py port:=/dev/ttyACM0
```

El dispositivo debe ser accesible por el usuario (habitualmente grupo `dialout`).
No ejecutar dos programas serie sobre el mismo puerto. El hardware real no
se ha probado conectado; se verificó el plugin con un pseudoterminal.

### Alexa

El servidor ROS de tareas funciona sin Alexa. La integración Alexa se activa
explícitamente porque requiere un identificador de skill y un endpoint HTTPS
configurado en la consola Alexa, como en el original.

```bash
cd ~/robot-programming
python3 -m venv --system-site-packages .venv-alexa
.venv-alexa/bin/python -m pip install -r src/arm_remote/requirements-alexa.txt
.venv-alexa/bin/python -m pip install --force-reinstall --no-deps \
  "oscrypto @ git+https://github.com/wbond/oscrypto.git@d5f3437ed24257895ae1edd9e503cfb352e635a8"
source .venv-alexa/bin/activate
source /opt/ros/jazzy/setup.bash
source install_jazzy/setup.bash
export ALEXA_SKILL_ID='amzn1.ask.skill.TU_IDENTIFICADOR'
ros2 launch arm_bringup simulated_robot.launch.py enable_alexa:=true
```

El servicio Flask escucha en `127.0.0.1:5000` (puerto configurable mediante
`ALEXA_PORT`). Conservar la verificación de firma y fecha del SDK cuando se
configure el acceso HTTPS. Intents originales: `WakeIntent`, `PickIntent`,
`SleepIntent`, además de `LaunchRequest`.

### Ejemplos restaurados

`arm_py_examples`: publicador, suscriptor, parámetros, cliente/servidor de
servicios y acciones Fibonacci. Ejecutar con `ros2 run arm_py_examples NOMBRE`;
los nombres son `simple_publisher`, `simple_subscriber`, `simple_parameter`,
`simple_service_server`, `simple_service_client`, `simple_action_server`,
`simple_action_client`.

`arm_cpp_examples`: equivalentes C++, además de `simple_lifecycle_node` y
`simple_moveit_interface`. Los ejecutables de acciones son
`simple_action_server_node` y `simple_action_client_node`.
El ejemplo MoveIt requiere el lanzamiento completo de simulación.

`arm_firmware`: `simple_serial_receiver`, `simple_serial_transmitter` y las
variantes `.py`, con parámetros `port` y `baudrate`; sketches de ejemplos
instalados en `share/arm_firmware/firmware`.

Las interfaces `Fibonacci` y `ArmTask` se añadieron a `arm_msgs`. Los servicios
de conversión de ángulos permanecen en `arm_utils`.

La copia de respaldo anterior permanece en el workspace local original; no se distribuye en este repositorio.

Validación y comparación detalladas: `migration/VALIDATION.md` y
`migration/COMPARISON.md`. Para un bringup completo sin ventanas:

```bash
ros2 launch arm_bringup simulated_robot.launch.py \
  gz_args:="-r -s $(ros2 pkg prefix --share arm_description)/worlds/arm_fast.sdf" use_rviz:=false
```

## Rendimiento en VMware

La simulación usa mallas ligeras, física de 4 ms, control a 50 Hz y RViz a 15 FPS.
Los colores se conservan. Las tareas y RViz usan un factor de velocidad y aceleración
de 0,3 en simulación. El hardware real conserva las mallas y configuración originales.
Las mallas simplificadas son aproximaciones; para estudios de contacto de precisión
se deben usar las mallas originales y un paso menor.

Mediciones y validación: [PERFORMANCE.md](../migration/PERFORMANCE.md).
