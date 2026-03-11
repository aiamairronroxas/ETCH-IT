import gerber
from gerber.primitives import Line, Circle, Rectangle, Region
import shapely.geometry as geom
from shapely.ops import unary_union
import math
from tkinter import messagebox

def generate_mill_gcode(file_path, logger=None, output_file="mill.nc", tool_dia=0.2, drill_depth=-0.05, travel_height=2.0):
    def log(msg):
        print(msg)
        if logger: logger(msg)

    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        layer = gerber.loads(content)
    except Exception as e:
        log(f"Error loading Gerber: {e}")
        return False

    polygons = []
    tool_radius = tool_dia / 2

    for p in layer.primitives:
        if isinstance(p, Region):
            pts = []
            for sub_p in p.primitives:
                if hasattr(sub_p, 'start'): pts.append(sub_p.start)
                if hasattr(sub_p, 'end'): pts.append(sub_p.end)
            if len(pts) > 2: polygons.append(geom.Polygon(pts).buffer(tool_radius))
        elif isinstance(p, Rectangle):
            x, y = p.position
            w, h = p.width, p.height
            polygons.append(geom.box(x-w/2, y-h/2, x+w/2, y+h/2).buffer(tool_radius))
        elif isinstance(p, Circle):
            polygons.append(geom.Point(p.position).buffer(p.radius + tool_radius))
        elif isinstance(p, Line):
            width = getattr(p.aperture, 'diameter', 0.2) if p.aperture else 0.2
            polygons.append(geom.LineString([p.start, p.end]).buffer((width/2) + tool_radius))

    if not polygons:
        log("Error: No valid shapes found.")
        return False

    log("Checking trace isolation...")
    has_collision = False
    for i in range(len(polygons)):
        for j in range(i + 1, len(polygons)):
            if polygons[i].intersects(polygons[j]):
                has_collision = True
                break
        if has_collision: break

    if has_collision:
        user_choice = messagebox.askyesno("Collision Warning", "Trace spacing is too narrow for tool. Proceed anyway?")
        if not user_choice:
            log("Process cancelled.")
            return False

    merged = unary_union(polygons)
    raw_paths = []
    geoms = merged.geoms if hasattr(merged, 'geoms') else [merged]
    for poly in geoms:
        if poly.geom_type == 'Polygon':
            raw_paths.append(list(poly.exterior.coords))
            for interior in poly.interiors:
                raw_paths.append(list(interior.coords))

    # TSP Optimization
    optimized_paths = []
    current_pos = (0, 0)
    while raw_paths:
        best_idx = min(range(len(raw_paths)), key=lambda i: math.dist(current_pos, raw_paths[i][0]))
        chosen_path = raw_paths.pop(best_idx)
        optimized_paths.append(chosen_path)
        current_pos = chosen_path[-1]

    try:
        with open(output_file, "w") as f:
            f.write("G21 ; mm\nG90 ; Absolute\nM3 S1000 ; Spindle ON\n")
            for path in optimized_paths:
                f.write(f"G0 X{path[0][0]:.4f} Y{path[0][1]:.4f} Z{travel_height}\n")
                f.write(f"G1 Z{drill_depth} F100\n")
                for x, y in path[1:]:
                    f.write(f"G1 X{x:.4f} Y{y:.4f} F75\n")
                f.write(f"G0 Z{travel_height}\n")
            f.write("G0 X0 Y0\nM30\n")
        log(f"Mill G-Code saved: {output_file}")
        return True
    except Exception as e:
        log(f"Write Error: {e}")
        return False