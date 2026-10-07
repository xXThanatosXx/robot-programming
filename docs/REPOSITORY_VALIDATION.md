# Validación del repositorio — 7 octubre 2026

- Script simulation_jazzy.sh: bash -n correcto.
- --check y --headless --check encuentran los recursos instalados.
- Lanzamiento real del script --headless en dominio ROS aislado 112:
  Gazebo, MoveIt, ros2_control y servidor de tareas inician.
- Objetivo inválido 99 rechazado; tareas 0, 1 y 2:
  status=4 (SUCCEEDED), success=true.
- Archivo .gitignore excluye build/install/log, venv, logs de pruebas,
  respaldos antiguos y archivos .env.
- GPL-3.0 del repositorio GitHub conservada; licencia Apache 2.0 de los paquetes
  originales incluida por separado, con sus autores y avisos.

Estas pruebas usan la instalación local Jazzy ya compilada. La compilación desde
un clon limpio en otro equipo y la conexión de motores físicos no se probaron
en esta preparación del repositorio.
