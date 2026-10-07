# Comparación Humble → Jazzy

Origen: https://github.com/xXThanatosXx/RoboticaIndustrial/tree/Robot-Arm-Real-Robot/arm_ws/src
Commit: b56023e15a0b34799ec461261acb91d5dafbb1bf

| Función original | Adaptación local |
|---|---|
| Gazebo Classic | Gazebo Harmonic, Ogre, reloj y recursos ROS-GZ |
| Visualización URDF y RViz | Conservada, colores añadidos |
| Controladores brazo/pinza | Conservados; joint_5 sigue mediante mimic, sin interfaz de comando |
| Arduino hardware_interface | Restaurado; API de inicialización Jazzy, buffers dimensionados, validación de límites |
| Puerto fijo /dev/ttyACM0 | Argumento port configurable |
| Firmware y ejemplos serie | Restaurados; parser protegido ante desbordamiento; sketches instalados |
| MoveIt | Configuración conservada; cabeceras Jazzy, tiempo simulado coherente |
| Tareas 0/1/2 | Restauradas; ejecución del plan, resultado de error, exclusión de tareas simultáneas, cancelación y feedback |
| Alexa | Intents originales; executor ROS, skill por variable de entorno, arranque opcional |
| Acciones Fibonacci/ArmTask | Restauradas |
| Ejemplos C++/Python | Todos restaurados; executor para ejemplo MoveIt |
| Bringup real/simulado | Restaurado con argumentos Jazzy y modo gráfico VMware |

Alexa requiere una skill externa y publicación HTTPS; se prueba localmente
el arranque y handlers. El Arduino físico requiere carga del sketch y USB;
la verificación local utiliza un pseudoterminal, sin motores conectados.

La integración Alexa usa el arreglo upstream de detección de OpenSSL en
https://github.com/wbond/oscrypto/commit/d5f3437ed24257895ae1edd9e503cfb352e635a8
y mantiene la validación del SDK.
