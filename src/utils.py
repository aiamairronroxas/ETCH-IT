# src/utils.py
import ctypes

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def rgb_to_hex(rgb):
    return '#%02x%02x%02x' % rgb

def draw_rounded_rect(canvas, x, y, w, h, r, color=None, gradient=None):
    canvas.delete("shape")
    if gradient:
        start_rgb = hex_to_rgb(gradient[0])
        end_rgb = hex_to_rgb(gradient[1])
        for i in range(int(w)):
            curr_rgb = tuple(int(start_rgb[j] + (end_rgb[j] - start_rgb[j]) * (i / w)) for j in range(3))
            curr_hex = rgb_to_hex(curr_rgb)
            canvas.create_line(x + i, y + r, x + i, y + h - r, fill=curr_hex, tags="shape")
            if r <= i <= w - r:
                canvas.create_line(x + i, y, x + i, y + r, fill=curr_hex, tags="shape")
                canvas.create_line(x + i, y + h - r, x + i, y + h, fill=curr_hex, tags="shape")
        # Corner ovals for gradient
        canvas.create_oval(x, y, x+r*2, y+r*2, fill=gradient[0], outline=gradient[0], tags="shape")
        canvas.create_oval(x+w-r*2, y, x+w, y+r*2, fill=gradient[1], outline=gradient[1], tags="shape")
        canvas.create_oval(x, y+h-r*2, x+r*2, y+h, fill=gradient[0], outline=gradient[0], tags="shape")
        canvas.create_oval(x+w-r*2, y+h-r*2, x+w, y+h, fill=gradient[1], outline=gradient[1], tags="shape")
    else:
        canvas.create_oval(x, y, x+r*2, y+r*2, fill=color, outline=color, tags="shape")
        canvas.create_oval(x+w-r*2, y, x+w, y+r*2, fill=color, outline=color, tags="shape")
        canvas.create_oval(x, y+h-r*2, x+r*2, y+h, fill=color, outline=color, tags="shape")
        canvas.create_oval(x+w-r*2, y+h-r*2, x+w, y+h, fill=color, outline=color, tags="shape")
        canvas.create_rectangle(x+r, y, x+w-r, y+h, fill=color, outline=color, tags="shape")
        canvas.create_rectangle(x, y+r, x+w, y+h-r, fill=color, outline=color, tags="shape")
    canvas.tag_lower("shape")

def apply_dark_title_bar(window):
    try:
        window.update()
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        # Dark mode attribute for Windows title bars
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(ctypes.c_int(2)), 4)
    except:
        pass