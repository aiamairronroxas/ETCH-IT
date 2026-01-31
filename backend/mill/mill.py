import gerber
import numpy as np
from matplotlib.patches import Polygon
from gerber.primitives import Line, Circle, Rectangle, Region
import matplotlib.pyplot as plt
import matplotlib.patches as patches

def plot_gerber(file_path):
    layer = gerber.read(file_path)
    fig, ax = plt.subplots(figsize=(10, 10))
    units = layer.units if layer.units else "mm"

    for primitive in layer.primitives:
        # 1. DRAW LINES (Traces)
        if isinstance(primitive, Line):
            plot_trace_as_filled_poly(ax, primitive)

    ax.set_aspect('equal', adjustable='datalim')
    ax.autoscale_view()
    ax.set_title(f"Visual Verification: {file_path}")
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
plot_gerber('drill_1_16.xln')