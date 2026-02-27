import gerber
from gerber.primitives import Line, Circle, Rectangle, Region
import shapely.geometry as geom
from shapely.ops import unary_union
import math

def generate_mill_gcode(file_path, output_file="isolation1.nc", tool_dia=0.5, drill_depth=-0.1, travel_height=2.0):
    try:
        # 1. Open the file manually to avoid the 'rU' mode error
        with open(file_path, 'r') as f:
            content = f.read()
        # 2. Pass the string content to gerber.read
        layer = gerber.loads(content)
    except Exception as e:
        print(f"Error: {e}")
        return False

    polygons = []
    tool_radius = tool_dia / 2

    # --- 1. Extraction (Using the 'Render' style logic you preferred) ---
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
        return False

    # --- 2. Merge and Extract Contours ---
    merged = unary_union(polygons)
    # Get list of all individual boundaries (LinearRings)
    raw_paths = []
    if hasattr(merged, 'geoms'):
        for poly in merged.geoms:
            raw_paths.append(list(poly.boundary.coords))
    else:
        raw_paths.append(list(merged.boundary.coords))

    # --- 3. Traveling Salesman (Nearest Neighbor) Optimization ---
    optimized_paths = []
    current_pos = (0, 0)

    while raw_paths:
        # Find the path whose first coordinate is closest to current_pos
        best_idx = 0
        min_dist = float('inf')
        
        for i, path in enumerate(raw_paths):
            d = math.dist(current_pos, path[0])
            if d < min_dist:
                min_dist = d
                best_idx = i
        
        # Pull the best path out of the list
        chosen_path = raw_paths.pop(best_idx)
        optimized_paths.append(chosen_path)
        # Update current position to the END of the path we just finished
        current_pos = chosen_path[-1]

    # --- 4. Write G-Code ---
    with open(output_file, "w") as f:
        f.write("G21 ; mm\nG90 ; Absolute\nM3 S1000 ; Spindle ON\n")
        
        for path in optimized_paths:
            # Rapid to Start
            f.write(f"G0 X{path[0][0]:.4f} Y{path[0][1]:.4f} Z{travel_height}\n")
            # Plunge
            f.write(f"G1 Z{drill_depth} F100\n")
            # Cut
            for x, y in path[1:]:
                f.write(f"G1 X{x:.4f} Y{y:.4f} F200\n")
            # Lift
            f.write(f"G0 Z{travel_height}\n")

        f.write("G0 X0 Y0\nM30\n")

    print(f"Success! {len(optimized_paths)} paths optimized and saved.")
    return True

