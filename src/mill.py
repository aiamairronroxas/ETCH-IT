import gerber
import numpy as np
from matplotlib.patches import Polygon
from gerber.primitives import Line, Circle, Rectangle, Region
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os

def plot_gerber(file_path):
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        layer = gerber.loads(content)
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    # 1. Set Fixed Resolution (1000x800)
    width_px, height_px = 1000, 800
    dpi = 100
    fig, ax = plt.subplots(figsize=(width_px/dpi, height_px/dpi), dpi=dpi)
    
    for primitive in layer.primitives:
        if isinstance(primitive, Line):
            plot_trace_as_filled_poly(ax, primitive)
        elif isinstance(primitive, Circle):
            radius = getattr(primitive, 'radius', None)
            if radius is None:
                radius = primitive.aperture.diameter / 2
            ax.add_patch(patches.Circle(primitive.position, radius, color='black'))
        elif isinstance(primitive, Rectangle):
            width = primitive.width
            height = primitive.height
            xy = (primitive.position[0] - width/2, primitive.position[1] - height/2)
            ax.add_patch(patches.Rectangle(xy, width, height, color='black'))
        elif isinstance(primitive, Region):
            points = []
            for sub_p in primitive.primitives:
                if isinstance(sub_p, Line):
                    points.append(sub_p.start)
                    points.append(sub_p.end)
            if points:
                poly = Polygon(points, color='black', closed=True)
                ax.add_patch(poly)

    ax.set_aspect('equal', adjustable='datalim')
    ax.autoscale_view()
    ax.set_title(f"Gerber Mill Verification: {os.path.basename(file_path)}")

    # 2. Center the Window on Screen
    mngr = plt.get_current_fig_manager()
    screen_w = mngr.window.winfo_screenwidth()
    screen_h = mngr.window.winfo_screenheight()
    x = int((screen_w - width_px) / 2)
    y = int((screen_h - height_px) / 2)
    mngr.window.geometry(f"{width_px}x{height_px}+{x}+{y}")
    
    plt.show()

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
    
    poly = Polygon([p1, p2, p3, p4], color='black', antialiased=True)
    ax.add_patch(poly)
    ax.add_patch(patches.Circle(start, width/2, color='black'))
    ax.add_patch(patches.Circle(end, width/2, color='black'))