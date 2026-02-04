import gerber
import shapely
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

def generate_mill_gcode(layer_path, output_file="isolation.nc", tool_dia=0.2, drill_depth=-0.1, travel_height=2.0):
    # 1. Load the Gerber file
    layer = gerber.read(layer_path)
    polygons = []

    print(f"Processing {layer_path} for isolation routing...")

    # 2. Convert Gerber primitives to Shapely Polygons
    for p in layer.primitives:
        # 1. Handle Traces (Lines)
        if hasattr(p, 'start') and hasattr(p, 'end'):
            line = LineString([p.start, p.end])
            # Safely get diameter from aperture, or default to 0.2
            aperture = getattr(p, 'aperture', None)
            trace_width = getattr(aperture, 'diameter', 0.2) if aperture else 0.2
            
            poly = line.buffer((trace_width / 2) + (tool_dia / 2))
            polygons.append(poly)
            
        # 2. Handle Circular Pads
        elif hasattr(p, 'position') and hasattr(p, 'aperture'):
            # This handles standard flashed circles/pads
            point = Point(p.position)
            pad_dia = p.aperture.diameter if hasattr(p.aperture, 'diameter') else 0.5
            poly = point.buffer((pad_dia / 2) + (tool_dia / 2))
            polygons.append(poly)

        # 3. Handle Polygon Primitives (Octagons/Regions)
        elif hasattr(p, 'points'):
            # This replaces the "skip" logic by actually processing the shape
            # p.points is a list of (x, y) tuples provided by the gerber library
            poly_shape = Polygon(p.points)
            
            # Buffer it by the tool radius for the isolation path
            isolation_poly = poly_shape.buffer(tool_dia / 2)
            polygons.append(isolation_poly)
            
        else:
            print(f"Skipping unknown primitive type: {type(p).__name__}")

    # 3. Merge overlapping paths into a single unified geometry
    merged_copper = unary_union(polygons)
    
    # We want to mill the BOUNDARY (the edge) of the copper
    toolpaths = merged_copper.boundary  

    # 4. Write G-code
    with open(output_file, "w") as f:
        # Header
        f.write("G21 ; Units: mm\n")
        f.write("G90 ; Absolute positioning\n")
        f.write(f"G0 Z{travel_height} ; Lift tool\n")

        # Handle multiple disconnected paths (MultiLineString or LineString)
        if hasattr(toolpaths, 'geoms'):
            paths = toolpaths.geoms
        else:
            paths = [toolpaths]

        for path in paths:
            coords = list(path.coords)
            if not coords: continue

            # Move to start of path
            f.write(f"G0 X{coords[0][0]:.4f} Y{coords[0][1]:.4f}\n")
            # Plunge
            f.write(f"G1 Z{drill_depth} F100\n")
            
            # Cut path
            for x, y in coords[1:]:
                f.write(f"G1 X{x:.4f} Y{y:.4f} F200\n")
            
            # Lift tool
            f.write(f"G0 Z{travel_height}\n")

        # Footer
        f.write("G0 X0 Y0 ; Return home\n")
        f.write("M30 ; End of program\n")

    print(f"Success! G-code saved to {output_file}")

# --- Execute ---
# Using the file visible in your sidebar
generate_mill_gcode('copper_bottom.gbr')