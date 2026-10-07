# Validación de la migración

Fecha: 2026-10-07. Ubuntu 24.04, ROS 2 Jazzy, Gazebo Harmonic en VMware.

- Los 10 paquetes compilan con colcon.
- rosdep confirma todas las dependencias del sistema satisfechas.
- Todos los archivos de los paquetes originales tienen equivalente local.
- URDF real: plugin armInterface, cuatro articulaciones controladas, puerto
  configurable y sin plugin Gazebo. URDF simulado mantiene mimic y colores.
- Plugin real cargado por controller_manager con un pseudoterminal: trayectoria
  de joint_1 a 0.1 rad transmite `b095,s090,e090,g000,`, compatible con Arduino.
- Servicios AddTwoInts C++ y Python: 3 + 4 = 7.
- Acciones Fibonacci C++ y Python: orden 4 devuelve [0, 1, 1, 2, 3].
- Bringup completo: los tres controladores se activan y MoveIt arranca.
- ArmTask 0, 1 y 2: resultado SUCCEEDED con success=true para las tres,
  ejecutadas consecutivamente en simulación.
- ArmTask: tarea inválida y tarea simultánea rechazadas; cancelación termina
  con estado CANCELED.
- Alexa: servidor Flask arranca y los handlers Wake/Pick/Sleep/Launch envían
  tareas 0/1/2/0. Prueba de handlers con cliente ROS sustituido por un registro;
  no constituye una prueba con el servicio externo Alexa.

Las comprobaciones serie y tareas se pueden repetir con los scripts vecinos
`verify_serial.py` y `verify_tasks.py`, después de cargar el entorno Jazzy.
El script serie crea su propio puerto emulado y dominio ROS 94; no usa Arduino.
El script de tareas requiere el bringup simulado y comparte su ROS_DOMAIN_ID.

No se ha cargado ni compilado el sketch para una placa concreta, ni conectado
un Arduino con motores. Alexa necesita ALEXA_SKILL_ID y un endpoint HTTPS
externo configurado. No hay sensor 3D en el modelo, por lo que el aviso de
Octomap no afecta a las pruebas de planificación por articulaciones.

Al cerrar la última prueba con SIGINT, el ejecutable binario `move_group`
de esta instalación mostró un fallo durante su destrucción y launch tuvo que
terminarlo. Las tareas y la cancelación habían finalizado correctamente;
este cierre no se considera validado. También se observó un proceso servidor
Gazebo que sobrevivió a su lanzador Ruby y se terminó como parte de la limpieza
de la prueba. Conservar esta limitación al evaluar el comportamiento al cerrar.

El fallo de cierre se reprodujo arrancando únicamente `arm_moveit` (sin
Gazebo, hardware ni servidor de tareas). La traza apunta al destructor de
`rclcpp::Executor` del binario MoveIt 2.12.4 instalado. Se conserva la traza
en `moveit-shutdown-validation.log`; el fallo sigue pendiente en esa instalación.
