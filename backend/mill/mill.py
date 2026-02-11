import gerber
import numpy as np
from matplotlib.patches import Polygon
from gerber.primitives import Line, Circle, Rectangle, Region
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def plot_gerber(file_path):
    try:
        layer = gerber.read(file_path)
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    fig, ax = plt.subplots(figsize=(10, 10))
    
    for primitive in layer.primitives:
        # 1. TRACES (Lines)
        if isinstance(primitive, Line):
            plot_trace_as_filled_poly(ax, primitive)

        # 2. CIRCULAR PADS (Vias, circular SMD pads)
        elif isinstance(primitive, Circle):
            # Gerber Circle primitives have 'position' and 'radius' or use aperture diameter
            radius = getattr(primitive, 'radius', None)
            if radius is None:
                radius = primitive.aperture.diameter / 2
            ax.add_patch(patches.Circle(primitive.position, radius, color='black'))

        # 3. RECTANGULAR PADS (Resistors, Capacitors, IC pins)
        elif isinstance(primitive, Rectangle):
            # Rectangle primitives are defined by center (position) and dimensions
            width = primitive.width
            height = primitive.height
            # Calculate bottom-left corner for matplotlib
            xy = (primitive.position[0] - width/2, primitive.position[1] - height/2)
            ax.add_patch(patches.Rectangle(xy, width, height, color='black'))

        # 4. COMPLEX PADS & COPPER POURS (Regions)
        elif isinstance(primitive, Region):
            # A Region is a list of primitives (usually lines and arcs) forming a loop
            # We extract the vertices to create a single filled Polygon
            points = []
            for sub_p in primitive.primitives:
                if isinstance(sub_p, Line):
                    points.append(sub_p.start)
                    points.append(sub_p.end)
            
            if points:
                # Remove duplicates while preserving order to keep the path clean
                poly = Polygon(points, color='black', closed=True)
                ax.add_patch(poly)

    ax.set_aspect('equal', adjustable='datalim')
    ax.autoscale_view()
    plt.show()

def plot_trace_as_filled_poly(ax, primitive):
    start = np.array(primitive.start)
    end = np.array(primitive.end)
    
    # Correctly grab width from the aperture
    try:
        width = primitive.aperture.width if primitive.aperture else 0.2
    except AttributeError:
        # Some circular apertures use 'diameter' even for lines
        width = getattr(primitive.aperture, 'diameter', 0.2)
    
    v = end - start
    dist = np.linalg.norm(v)
    if dist == 0: return 
    
    n = np.array([-v[1], v[0]]) / dist
    p1, p2 = start + n * (width/2), end + n * (width/2)
    p3, p4 = end - n * (width/2), start - n * (width/2)
    
    poly = Polygon([p1, p2, p3, p4], color='black', antialiased=True)
    ax.add_patch(poly)
    
    # OPTIONAL: Add rounded caps to match physical Gerber traces
    ax.add_patch(patches.Circle(start, width/2, color='black'))
    ax.add_patch(patches.Circle(end, width/2, color='black'))

# Run the function
# FOR TESTING PURPOSES ONLY
plot_gerber('copper_bottom.gbr')