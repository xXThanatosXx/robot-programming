# Rendimiento de simulación — 7 octubre 2026

VMware, 4 CPU virtuales, 8 GB RAM, SVGA3D; glxinfo informa Accelerated: no.

| Medición de /clock durante 10 s reales | Factor de tiempo real |
|---|---:|
| Configuración anterior, Gazebo sin GUI | 0,234 |
| Configuración optimizada, inicio sin GUI | 0,985 |
| Configuración optimizada, Gazebo GUI y RViz abiertos | 0,997 |

La primera ventana optimizada coincide con el arranque de MoveIt/RViz.
Estas mediciones corresponden al equipo actual y no garantizan el mismo resultado
bajo otra carga de CPU o durante contactos complejos.

Cambios:
- Mundo arm_fast.sdf: paso de física 4 ms frente a 1 ms; sombras desactivadas;
  sin sistema Contact, pues el modelo no tiene sensores de contacto.
- Mallas visuales: 167532 → 51938 triángulos
  (69.0 % menos). También se simplifican las colisiones.
  El generador comprueba diferencias de límites menores del 1 % de la extensión
  máxima y de volumen menores del 3 %. Esto no prueba equivalencia de contactos.
- Control simulado: 50 Hz frente a 10 Hz.
- RViz: 15 FPS; animación de trayectoria sin repetición automática.
- Factores de velocidad/aceleración de RViz y ArmTask: 0,3 frente a 0,1,
  únicamente en simulación. Los límites articulares permanecen iguales.
- Robot físico: mallas originales y configuración original de control/RViz.

Validación: compilación de los cinco paquetes afectados, expansión de xacro para
simulación y hardware real; tres controladores activos; ArmTask 0, 1 y 2 con
status SUCCEEDED y success=true; objetivo inválido 99 rechazado.
Colores de materiales conservados. Registros en performance_logs/.

Las mallas originales permanecen en meshes/. Xacro permite mesh_quality:=original.
Para estudios de dinámica/contacto de precisión, usar originales y paso de física
menor. El mundo previo continúa disponible con gz_args:='-r empty.sdf'.
El script scripts/optimize_meshes.py solo sirve para regenerar los assets; requiere
trimesh, numpy y fast-simplification, no necesarios para ejecutar el robot.
