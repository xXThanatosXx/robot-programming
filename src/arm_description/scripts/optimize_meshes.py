#!/usr/bin/env python3
"""Generate lightweight STL assets. Requires trimesh and fast-simplification."""
from pathlib import Path
import json
import numpy as np
import trimesh

root = Path(__file__).resolve().parents[1] / 'meshes'
used = ['basement', 'base_plate', 'forward_drive_arm', 'horizontal_arm',
        'claw_support', 'right_finger', 'left_finger']
report = []
for name in used:
    original = trimesh.load_mesh(root / f'{name}.STL', process=True)
    for kind, budget in [('visual', 3000), ('collision', 2000)]:
        result = original.copy()
        while budget < len(original.faces):
            result = original.simplify_quadric_decimation(face_count=budget)
            bounds_ok = np.max(np.abs(result.bounds - original.bounds)) < max(original.extents) * .01
            volume_ok = (abs(original.volume) < 1e-9 or
                         abs(result.volume - original.volume) / abs(original.volume) < .03)
            if bounds_ok and volume_ok:
                break
            budget *= 2
        else:
            result = original.copy()
        assert np.isfinite(result.vertices).all()
        assert np.max(np.abs(result.bounds - original.bounds)) < max(original.extents) * .01
        folder = root / 'optimized' / kind
        folder.mkdir(parents=True, exist_ok=True)
        result.export(folder / f'{name}.STL')
        report.append({'mesh': name, 'kind': kind, 'original_triangles': len(original.faces),
                       'optimized_triangles': len(result.faces)})
(root / 'optimized' / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2))
