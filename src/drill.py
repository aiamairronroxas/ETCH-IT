import gerber
from gerber.primitives import Circle
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os

def plot_drill_layer(ax, file_path):
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        layer = gerber.loads(content)
    except Exception as e:
        print(f"Error in plot_drill_layer: {e}")
        return
    
    for primitive in layer.primitives:
        if isinstance(primitive, Circle) or hasattr(primitive, 'position'):
            pos = primitive.position
            d = 0.5  # Default drill size
            hole = patches.Circle(pos, d/2, color='red', fill=True, alpha=0.9, zorder=5)
            ax.add_patch(hole)

def plot_excellon(file_path):
    # 1. Set Fixed Resolution (1000x800)
    width_px, height_px = 1000, 800
    dpi = 100
    fig, ax = plt.subplots(figsize=(width_px/dpi, height_px/dpi), dpi=dpi)
    
    plot_drill_layer(ax, file_path)
    
    ax.relim()
    ax.autoscale_view()
    ax.set_aspect('equal')
    ax.set_title(f"Excellon Drill Verification: {os.path.basename(file_path)}")
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    plt.grid(True, linestyle=':', alpha=0.5)
    
    # 2. Center the Window on Screen
    mngr = plt.get_current_fig_manager()
    screen_w = mngr.window.winfo_screenwidth()
    screen_h = mngr.window.winfo_screenheight()
    x = int((screen_w - width_px) / 2)
    y = int((screen_h - height_px) / 2)
    mngr.window.geometry(f"{width_px}x{height_px}+{x}+{y}")
    
    plt.show()