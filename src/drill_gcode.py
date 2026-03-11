import gerber
import math

def generate_drill_gcode(file_path, output_file="drill.nc", safe_z=2.0, drill_z=-1.45):
    try:
        # 1. Open the file manually to avoid the 'rU' mode error
        with open(file_path, 'r') as f:
            content = f.read()
        # 2. Pass the string content to gerber.read
        layer = gerber.loads(content)
    except Exception as e:
        print(f"Error reading file: {e}")
        return False

    # 1. Collect all raw points first
    raw_points = []
    for p in layer.primitives:
        if hasattr(p, 'position'):
            raw_points.append(p.position)   
        elif hasattr(p, 'x') and hasattr(p, 'y'):
            raw_points.append((p.x, p.y))

    if not raw_points:
        print("No holes found.")
        return False

    # 2. Nearest Neighbor Sorting
    # Start at (0,0) or the first point
    optimized_points = []
    current_pos = (0, 0)
    
    while raw_points:
        # Find the point in raw_points closest to current_pos
        nearest_pt = min(raw_points, key=lambda pt: math.dist(current_pos, pt))
        optimized_points.append(nearest_pt)
        raw_points.remove(nearest_pt)
        current_pos = nearest_pt

    # 3. Write the G-code in the optimized order
    try:
        with open(output_file, "w") as f:
            f.write(f"; Optimized Drill G-code\n")
            f.write("G21 ; mm\nG90 ; Absolute\nM3 S1000 ; Spindle ON\n")
            f.write(f"G0 Z{safe_z}\n")

            for x, y in optimized_points:
                f.write(f"G0 X{x:.4f} Y{y:.4f}\n")
                f.write(f"G1 Z{drill_z} F100\n")
                f.write(f"G0 Z{safe_z}\n")

            f.write("M5 ; Spindle OFF\nG0 X0 Y0\nM30\n")
            
        print(f"Success! {len(optimized_points)} holes optimized.")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False