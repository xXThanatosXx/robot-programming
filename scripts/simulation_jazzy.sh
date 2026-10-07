#!/usr/bin/env bash
# Ejecutar; no usar "source". Configuración optimizada limitada a este proceso.
set -eo pipefail

usage() {
  cat <<'HELP'
Uso: ./scripts/simulation_jazzy.sh [--headless | --no-rviz] [--check]
  Sin opciones: Gazebo + controladores + MoveIt + RViz + ArmTask.
  --no-rviz:   Gazebo gráfico, MoveIt y ArmTask sin RViz.
  --headless:  Gazebo servidor, MoveIt y ArmTask sin ventanas.
  --check:     comprueba entorno y recursos; no inicia nodos.
  --help:      muestra esta ayuda.
Variables opcionales: ARM_WS, ARM_RENDER_ENGINE (ogre por defecto).
HELP
}

headless=false
use_rviz=true
check=false
for arg in "$@"; do
  case "$arg" in
    --headless) headless=true; use_rviz=false ;;
    --no-rviz) use_rviz=false ;;
    --check) check=true ;;
    --help|-h) usage; exit 0 ;;
    *) printf 'Opción desconocida: %s\n' "$arg" >&2; usage >&2; exit 2 ;;
  esac
done
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
workspace="${ARM_WS:-$(cd -- "$script_dir/.." && pwd)}"
for setup in /opt/ros/jazzy/setup.bash "$workspace/install_jazzy/setup.bash"; do
  if [[ ! -r "$setup" ]]; then
    printf 'Falta %s. Instala Jazzy y compila el workspace según README.md.\n' "$setup" >&2
    exit 1
  fi
done
# Los setup ROS pueden leer variables no definidas: activar nounset después.
source /opt/ros/jazzy/setup.bash
source "$workspace/install_jazzy/setup.bash"
set -u
export QT_QPA_PLATFORM=xcb
description="$(ros2 pkg prefix --share arm_description)"
moveit="$(ros2 pkg prefix --share arm_moveit)"
controller="$(ros2 pkg prefix --share arm_controller)"
world="$description/worlds/arm_fast.sdf"
for asset in "$world" "$description/config/gazebo_vm.config" \
             "$description/meshes/optimized/report.json" \
             "$moveit/config/moveit_vm.rviz" "$controller/config/arm_controllers_sim.yaml"; do
  [[ -r "$asset" ]] || { printf 'Recurso ausente: %s\n' "$asset" >&2; exit 1; }
done
gz_args="-r $world"
if [[ "$headless" == true ]]; then gz_args="-r -s $world"; fi
printf 'Jazzy optimizado: física 4 ms, control 50 Hz, RViz 15 FPS, factor de movimiento 0.3.\n'
printf 'Workspace: %s\nModo: headless=%s, RViz=%s, motor=%s\n' \
  "$workspace" "$headless" "$use_rviz" "${ARM_RENDER_ENGINE:-ogre}"
if [[ "$check" == true ]]; then exit 0; fi
exec ros2 launch arm_bringup simulated_robot.launch.py \
  "gz_args:=$gz_args" "use_rviz:=$use_rviz" \
  "render_engine:=${ARM_RENDER_ENGINE:-ogre}"
