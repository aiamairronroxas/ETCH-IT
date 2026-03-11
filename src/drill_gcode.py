import gerber
import math

def generate_drill_gcode(file_path, logger=None, output_file="drill.nc", safe_z=2.0, drill_z=-1.45):
    def log(msg):
        print(msg)
        if logger: logger(msg)

    try:
        # Use utf-8 and ignore errors to prevent crashes on legacy files
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        layer = gerber.loads(content)
    except Exception as e:
        log(f"Error reading drill file: {e}")
        return False

    raw_points = []
    for p in layer.primitives:
        if hasattr(p, 'position'):
            raw_points.append(p.position)   
        elif hasattr(p, 'x') and hasattr(p, 'y'):
            raw_points.append((p.x, p.y))

    if not raw_points:
        log("No holes found in file.")
        return False

    # Nearest Neighbor Sorting
    optimized_points = []
    current_pos = (0, 0)
    
    log(f"Optimizing {len(raw_points)} drill hits...")
    while raw_points:
        nearest_pt = min(raw_points, key=lambda pt: math.dist(current_pos, pt))
        optimized_points.append(nearest_pt)
        raw_points.remove(nearest_pt)
        current_pos = nearest_pt

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
            
        log(f"Success! {len(optimized_points)} holes saved to {output_file}")
        return True
    except Exception as e:
        log(f"Write Error: {e}")
        return False