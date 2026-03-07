import gerber
import math

def generate_drill_gcode(file_path, output_file="drill.nc", tool_dia=0.5, safe_z=2.0, drill_z=-1.5):
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        layer = gerber.loads(content)
    except Exception as e:
        print(f"Error reading file: {e}")
        return False

    drill_ops = [] # Store as (x, y, hole_dia)
    
    for p in layer.primitives:
        # pcb-tools Drill primitives usually have a 'diameter' attribute
        dia = getattr(p, 'diameter', tool_dia)
        if hasattr(p, 'position'):
            drill_ops.append((p.position[0], p.position[1], dia))

    if not drill_ops:
        return False

    # Sorting logic (Nearest Neighbor)
    optimized_ops = []
    current_pos = (0, 0)
    while drill_ops:
        nearest = min(drill_ops, key=lambda op: math.dist(current_pos, (op[0], op[1])))
        optimized_ops.append(nearest)
        drill_ops.remove(nearest)
        current_pos = (nearest[0], nearest[1])

    with open(output_file, "w") as f:
        f.write("; Helical Drill G-code\nG21 ; mm\nG90 ; Absolute\nM3 S1000\n")
        
        for x, y, hole_dia in optimized_ops:
            f.write(f"G0 X{x:.4f} Y{y:.4f}\n") # Move to center
            
            if hole_dia <= tool_dia:
                # Standard plunge for small holes
                f.write(f"G1 Z{drill_z} F100\n")
            else:
                # Helical/Circular move for larger holes
                offset = (hole_dia - tool_dia) / 2
                # 1. Move to the edge of the circle
                f.write(f"G0 X{x + offset:.4f} Y{y:.4f}\n")
                # 2. Plunge
                f.write(f"G1 Z{drill_z} F100\n")
                # 3. Cut the circle (G2 is clockwise, I is the X-offset to center)
                f.write(f"G2 X{x + offset:.4f} Y{y:.4f} I{-offset:.4f} J0 F200\n")
            
            f.write(f"G0 Z{safe_z}\n")

        f.write("M5\nG0 X0 Y0\nM30\n")
    return True