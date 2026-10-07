# Robot Programming

Brazo robótico para **Ubuntu 24.04, ROS 2 Jazzy y Gazebo Harmonic**.
Incluye simulación optimizada para VMware, MoveIt 2, RViz, tareas ROS y
control real por Arduino USB. Migración del proyecto Humble
[RoboticaIndustrial](https://github.com/xXThanatosXx/RoboticaIndustrial/tree/Robot-Arm-Real-Robot/arm_ws/src).

## 1. Instalar ROS 2 Jazzy y herramientas

En una instalación nueva de Ubuntu 24.04, configurar primero el repositorio APT
de ROS siguiendo la [guía oficial de Jazzy](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html).
Luego ejecutar:

```bash
sudo apt update
sudo apt install -y ros-jazzy-desktop python3-colcon-common-extensions \
  python3-rosdep python3-venv git build-essential cmake
source /opt/ros/jazzy/setup.bash
```

Usar una terminal nueva sin cargar Humble.

## 2. Clonar e instalar los paquetes

```bash
git clone https://github.com/xXThanatosXx/robot-programming.git ~/robot-programming
cd ~/robot-programming
source /opt/ros/jazzy/setup.bash

# Inicializar rosdep solo si no se ha inicializado anteriormente.
if [ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]; then
  sudo rosdep init
fi
rosdep update
rosdep install --from-paths src --ignore-src --rosdistro jazzy -y

# Instalar/actualizar las bibliotecas concretas de control para evitar
# versiones mezcladas y errores como libpal_statistics.so ausente.
sudo apt install -y ros-jazzy-ros-gz ros-jazzy-gz-ros2-control \
  ros-jazzy-moveit ros-jazzy-tf-transformations \
  ros-jazzy-pal-statistics ros-jazzy-hardware-interface \
  ros-jazzy-controller-manager ros-jazzy-controller-interface \
  ros-jazzy-control-toolbox ros-jazzy-joint-trajectory-controller \
  ros-jazzy-joint-state-broadcaster ros-jazzy-ros2controlcli libserial-dev

colcon build --symlink-install --build-base build_jazzy --install-base install_jazzy
source install_jazzy/setup.bash
```

El repositorio es el workspace: contiene directamente `src/`.
No incluye archivos compilados ni entornos virtuales.

## 3. Entorno en cada terminal

Antes de los comandos de las siguientes etapas, ejecutar en **cada terminal**:

```bash
cd ~/robot-programming
source /opt/ros/jazzy/setup.bash
source install_jazzy/setup.bash
```

Usar el mismo `ROS_DOMAIN_ID` en todas las terminales.
Las etapas se ejecutan por separado: detener con `Ctrl+C` antes de cambiar
de modo para evitar nodos o controladores duplicados.

## 4. Simulación completa optimizada

### Terminal 1: iniciar todos los componentes

El script carga Jazzy y el workspace automáticamente:

```bash
cd ~/robot-programming
./scripts/simulation_jazzy.sh --check
./scripts/simulation_jazzy.sh
```

Inicia Gazebo, robot_state_publisher, puente /clock, tres controladores,
MoveIt, RViz y servidor /task_server. Esperar a que los controladores estén activos.

### Terminal 2: comprobar y ejecutar las tareas

Cargar el entorno indicado en la sección 3 y ejecutar:

```bash
ros2 control list_controllers
ros2 action list -t
ros2 interface show arm_msgs/action/ArmTask

# 0: posición inicial y pinza abierta
ros2 action send_goal /task_server arm_msgs/action/ArmTask '{task_number: 0}' --feedback
# 1: recoger
ros2 action send_goal /task_server arm_msgs/action/ArmTask '{task_number: 1}' --feedback
# 2: reposo
ros2 action send_goal /task_server arm_msgs/action/ArmTask '{task_number: 2}' --feedback
```

Enviar una tarea por vez y esperar su resultado.
Los controladores `joint_state_broadcaster`, `arm_controller` y
`gripper_controller` deben aparecer `active`.
En RViz, seleccionar el grupo `arm` o `gripper`, ajustar objetivo y
usar **Plan** y **Execute**.

### Modos con menos consumo

```bash
# Gazebo con ventana, sin RViz:
./scripts/simulation_jazzy.sh --no-rviz

# Sin ventanas; las tareas siguen disponibles desde otra terminal:
./scripts/simulation_jazzy.sh --headless
```

No ejecutar estos modos simultáneamente.
Equivalente al modo completo sin script, después de cargar el entorno:

```bash
ros2 launch arm_bringup simulated_robot.launch.py
```

## 5. Simulación por etapas

Esta es una alternativa al lanzamiento completo de la sección 4.

### Etapa A: visualizar el modelo sin física

```bash
ros2 launch arm_description display.launch.py
```

Detener esta etapa antes de continuar.

### Etapa B: Gazebo y controladores — terminal 1

```bash
ros2 launch arm_controller simulation.launch.py
```

### Etapa C: planificación MoveIt y RViz — terminal 2

```bash
ros2 control list_controllers
ros2 launch arm_moveit moveit.launch.py is_sim:=true
```

### Etapa D: servidor de tareas — terminal 3

```bash
ros2 launch arm_remote remote_interface.launch.py is_sim:=true
```

### Etapa E: comandos — terminal 4

Enviar los objetivos 0, 1 y 2 de la sección 4.
Mantener abiertas las terminales de las etapas B, C y D.

### Alternativa: control manual por deslizadores

Detener los lanzamientos anteriores. Terminal 1:

```bash
ros2 launch arm_description gazebo.launch.py
```

Terminal 2:

```bash
ros2 launch arm_controller slider_controller.launch.py
```

Esta alternativa inicia sus propios spawners; no combinarla con
`simulation.launch.py` ni con el bringup completo.

## 6. Robot real

### Etapa A: cargar firmware

Abrir en Arduino IDE:

```text
src/arm_firmware/firmware/robot_control/robot_control.ino
```

Instalar la biblioteca **Servo**, elegir la placa Arduino y su puerto y cargar
el sketch. Pines: base **8**, hombro **9**, codo **10**, pinza **11**;
serie **115200 baudios**. En VMware conectar el USB al sistema invitado.
El firmware posiciona los servos al arrancar; preparar el brazo antes de conectarlo.

### Etapa B: permisos y puerto USB

```bash
sudo usermod -aG dialout "$USER"
```

Cerrar sesión y volver a entrar para aplicar el grupo. Después:

```bash
ls -l /dev/serial/by-id/
ls -l /dev/ttyACM* /dev/ttyUSB* 2>/dev/null
id -nG
```

Los ejemplos usan `/dev/ttyACM0`; sustituirlo por el puerto real, preferiblemente
una ruta estable de `/dev/serial/by-id/`. Cerrar el monitor serie de Arduino.

### Etapa C: inicio completo — terminal 1

Cargar el entorno de la sección 3:

```bash
ros2 launch arm_bringup real_robot.launch.py port:=/dev/ttyACM0
```

### Etapa D: comprobar y ejecutar — terminal 2

```bash
ros2 control list_controllers
ros2 topic echo /joint_states --once

ros2 action send_goal /task_server arm_msgs/action/ArmTask '{task_number: 0}' --feedback
ros2 action send_goal /task_server arm_msgs/action/ArmTask '{task_number: 1}' --feedback
ros2 action send_goal /task_server arm_msgs/action/ArmTask '{task_number: 2}' --feedback
```

Enviar una tarea por vez. RViz también permite planificar y ejecutar.

### Alternativa: robot real por etapas

Detener el bringup completo. Cargar el entorno en las tres terminales.

Terminal 1, hardware y controladores:

```bash
ros2 launch arm_controller controller.launch.py is_sim:=false port:=/dev/ttyACM0
```

Terminal 2, MoveIt y RViz:

```bash
ros2 launch arm_moveit moveit.launch.py is_sim:=false
```

Terminal 3, servidor de tareas:

```bash
ros2 launch arm_remote remote_interface.launch.py is_sim:=false
```

Terminal 4: comprobar controladores y enviar las mismas tareas.

El estado del robot real se estima a partir de los comandos: el firmware
original no transmite posiciones medidas. El plugin serie se verificó con un
pseudoterminal; las pruebas automáticas no certifican el movimiento de motores físicos.
No abrir el mismo puerto con varios programas.

## 7. Configuración optimizada de Jazzy

El archivo ejecutable [scripts/simulation_jazzy.sh](scripts/simulation_jazzy.sh)
selecciona los recursos optimizados versionados:

| Recurso | Configuración |
|---|---|
| Gazebo Harmonic | Ogre, Qt xcb, ventana 960 × 640 |
| Mundo arm_fast.sdf | Física 4 ms, sin sombras ni sistema de sensores Contact |
| Mallas visuales y de colisión | Mallas ligeras; originales conservadas |
| Control simulado | 50 Hz |
| RViz moveit_vm.rviz | 15 FPS, animación sin repetición |
| MoveIt/RViz y ArmTask simulado | Factores de velocidad y aceleración 0,3 |

Estas opciones se aplican a la simulación. El robot real conserva las mallas,
configuración de control y factores de movimiento originales.
En la VM probada, /clock pasó de 0,234 a aproximadamente 0,997 segundos simulados
por segundo real. Depende de la carga del equipo.
Las mallas aproximadas y el paso de 4 ms se orientan a control y visualización;
para estudios precisos de contacto usar originales y un paso de física menor.

El script funciona desde cualquier directorio y no modifica archivos del sistema.
Variables opcionales:

```bash
ARM_WS=~/robot-programming ./scripts/simulation_jazzy.sh --check
ARM_RENDER_ENGINE=ogre2 ./scripts/simulation_jazzy.sh
```

Ogre2 es opcional para equipos con aceleración gráfica compatible.
Mediciones: [migration/PERFORMANCE.md](migration/PERFORMANCE.md).

## 8. Alexa y ejemplos adicionales

Alexa es opcional: requiere un skill ID y un endpoint HTTPS configurado.
Ver comandos de instalación y activación en
[docs/JAZZY_MIGRATION.md](docs/JAZZY_MIGRATION.md#alexa).


Los paquetes `arm_cpp_examples` y `arm_py_examples` incluyen publicadores,
suscriptores, parámetros, servicios y acciones Fibonacci.
Los detalles están en [documentación de migración](docs/JAZZY_MIGRATION.md#ejemplos-restaurados).

## 9. Diagnóstico

```bash
ros2 doctor --report
ros2 control list_controllers
ros2 topic hz /joint_states
ros2 topic echo /clock --once
ros2 action info /task_server
```

- Si /controller_manager no aparece, revisar primero el error del plugin en Gazebo.
- Si falta libpal_statistics.so o hay símbolos incompatibles, actualizar las
  bibliotecas de la sección 2 y reiniciar todos los procesos ROS/Gazebo.
- Si no se abre el puerto real, revisar USB, dialout y monitor serie.
- Si la VM consume demasiados recursos, ejecutar `--no-rviz` o `--headless`.
- Detener los procesos con `Ctrl+C` en sus terminales.

Comparación y pruebas: [COMPARISON.md](migration/COMPARISON.md),
[VALIDATION.md](migration/VALIDATION.md).

## Licencia y origen

Licencia general GPL-3.0 elegida al crear el repositorio: [LICENSE](LICENSE).
Los paquetes derivados conservan sus avisos Apache-2.0 y autores originales;
la licencia original se incluye en [LICENSE-APACHE-2.0](LICENSE-APACHE-2.0).
Ver [NOTICE](NOTICE).
