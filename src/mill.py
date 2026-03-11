import gerber
import numpy as np
from gerber.primitives import Line, Circle, Rectangle, Region

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os
from matplotlib.patches import Polygon

def plot_trace_as_filled_poly(ax, primitive):
    start = np.array(primitive.start)
    end = np.array(primitive.end)
    try:
        width = primitive.aperture.width if primitive.aperture else 0.2
    except AttributeError:
        width = getattr(primitive.aperture, 'diameter', 0.2)
    
    v = end - start
    dist = np.linalg.norm(v)
    if dist == 0: return 
    
    n = np.array([-v[1], v[0]]) / dist
    p1, p2 = start + n * (width/2), end + n * (width/2)
    p3, p4 = end - n * (width/2), start - n * (width/2)
    
    ax.add_patch(Polygon([p1, p2, p3, p4], color='black', antialiased=True))
    ax.add_patch(patches.Circle(start, width/2, color='black'))
    ax.add_patch(patches.Circle(end, width/2, color='black'))

def plot_gerber(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        layer = gerber.loads(content)
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    width_px, height_px = 1000, 800
    dpi = 100
    fig, ax = plt.subplots(figsize=(width_px/dpi, height_px/dpi), dpi=dpi)
    
    for primitive in layer.primitives:
        if isinstance(primitive, Line):
            plot_trace_as_filled_poly(ax, primitive)
        elif isinstance(primitive, Circle):
            radius = getattr(primitive, 'radius', primitive.aperture.diameter / 2 if hasattr(primitive.aperture, 'diameter') else 0.1)
            ax.add_patch(patches.Circle(primitive.position, radius, color='black'))
        elif isinstance(primitive, Rectangle):
            w, h = primitive.width, primitive.height
            xy = (primitive.position[0] - w/2, primitive.position[1] - h/2)
            ax.add_patch(patches.Rectangle(xy, w, h, color='black'))
        elif isinstance(primitive, Region):
            points = [p.start for p in primitive.primitives if hasattr(p, 'start')]
            if points: ax.add_patch(Polygon(points, color='black', closed=True))

    ax.set_aspect('equal')
    ax.autoscale_view()
    ax.set_title(f"Mill Verification: {os.path.basename(file_path)}")
    
    mngr = plt.get_current_fig_manager()
    try:
        mngr.window.geometry(f"{width_px}x{height_px}")
    except:
        pass
        
    plt.show()