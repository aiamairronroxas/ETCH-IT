import gerber
from gerber.primitives import Line, Circle, Rectangle, Region
import shapely.geometry as geom
from shapely.ops import unary_union
import math

def generate_mill_gcode(file_path, logger=None, output_file="isolation1.nc", tool_dia=0.5, drill_depth=-0.1, travel_height=2.0):
    # Helper to handle both GUI logging and terminal printing
    def log(msg):
        print(msg)  # Still print to terminal for debugging
        if logger:
            logger(msg)

    try:
        # log(f"Opening Gerber file: {file_path}")
        with open(file_path, 'r') as f:
            content = f.read()
        layer = gerber.loads(content)
        log(f"Successfully loaded {len(layer.primitives)} Gerber primitives.")
    except Exception as e:
        log(f"Error loading Gerber: {e}")
        return False

    polygons = []
    tool_radius = tool_dia / 2

    # --- 1. Extraction ---
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
        log("Error: No valid shapes found to generate toolpaths.")
        return False

    # --- 2. Overlap Detection & Merging ---
    log(f"Checking for collisions.")
    has_collision = False
    for i in range(len(polygons)):
        for j in range(i + 1, len(polygons)):
            if polygons[i].intersects(polygons[j]):
                log(f"ERROR: Trace spacing too narrow for drill size!")
                #log(f"Isolation paths for primitives {i} and {j} overlap.")   # pinapakita kung anong primitive nagooverlap
                                                                               # which is di naman maiintindihan ng user
                has_collision = True
                break
        if has_collision: break

    if has_collision:
        log("Terminating: Overlapping boundaries detected. Increase copper trace spacing to continue.")
        return False

    # Proceed with merging only if no collisions found
    merged = unary_union(polygons)
    raw_paths = []
    
    geoms = merged.geoms if hasattr(merged, 'geoms') else [merged]
    for poly in geoms:
        if poly.geom_type == 'Polygon':
            raw_paths.append(list(poly.exterior.coords))
            for interior in poly.interiors:
                raw_paths.append(list(interior.coords))

    # --- 3. Traveling Salesman Optimization ---
    log(f"Optimizing {len(raw_paths)} toolpaths for shortest travel...")
    optimized_paths = []
    current_pos = (0, 0)

    while raw_paths:
        best_idx = 0
        min_dist = float('inf')
        for i, path in enumerate(raw_paths):
            d = math.dist(current_pos, path[0])
            if d < min_dist:
                min_dist = d
                best_idx = i
        
        chosen_path = raw_paths.pop(best_idx)
        optimized_paths.append(chosen_path)
        current_pos = chosen_path[-1]

    # --- 4. Write G-Code ---
    try:
        log(f"Writing G-Code to {output_file}...")
        with open(output_file, "w") as f:
            f.write("G21 ; mm\nG90 ; Absolute\nM3 S1000 ; Spindle ON\n")
            for path in optimized_paths:
                f.write(f"G0 X{path[0][0]:.4f} Y{path[0][1]:.4f} Z{travel_height}\n")
                f.write(f"G1 Z{drill_depth} F100\n")
                for x, y in path[1:]:
                    f.write(f"G1 X{x:.4f} Y{y:.4f} F200\n")
                f.write(f"G0 Z{travel_height}\n")
            f.write("G0 X0 Y0\nM30\n")
        
        log(f"Success! G-Code saved. Total paths: {len(optimized_paths)}")
        return True
    except Exception as e:
        log(f"File writing error: {e}")
        return False

