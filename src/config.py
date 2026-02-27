# src/config.py

COLORS = {
    "root_bg": "#000000",
    "sidebar_bg": "#FFFFFF",
    "main_content_bg": "#F5F5F5",
    "sidebar_text": "#6D6B6B",
    "nav_hover": "#F0F0F0",
    "accent_red": "#9a1e1a",
    "btn_hover_red": "#880505",
    "f1_grad_start": "#b81d1d",
    "f1_grad_end": "#f04135",
    "f2_grad_start": "#f68519",
    "f2_grad_end": "#ffe439",
    "f2_hover_start": "#e0740d",
    "f2_hover_end": "#f0d320",
    "f3_grad_start": "#1a73e8",
    "f3_grad_end": "#6fb1fc",
    "f3_hover_start": "#155db1",
    "f3_hover_end": "#63a0e6",
    "text_primary": "#333333",
    "text_secondary": "#666666",
    "btn_text_white": "#FFFFFF",
    "console_bg": "#FFFFFF"
}

FRAME_CONFIGS = {
    "f2_btn": {
        "width": 440, "height": 400, "pos_x": 90, "pos_y": 600,
        "corner_radius": 15, "text": "View Gerber", "text_color": "#FFFFFF",
        "font": ("Arial", 25, "bold"), "icon_path": "assets/upload.png",
        "icon_size": (35, 35), "spacing": 15
    },
    "f3_btn": {
        "width": 440, "height": 400, "pos_x": 550, "pos_y": 600,
        "corner_radius": 15, "text": "Etch-IT!", "text_color": "#FFFFFF",
        "font": ("Arial", 25, "bold"), "icon_path": "assets/cnc.png",
        "icon_size": (35, 35), "spacing": 15
    },
    "status": {
        "width": 380, "height": 840, "pos_x": 1020, "pos_y": 160,
        "corner_radius": 20
    },
    "standalone_icon": {
        "path": "assets/doodle.png",
        "size": (420, 1100),
        "pos_x": 1400,
        "pos_y": 1
    }
}

APP_SETTINGS = {
    "sidebar_rel_width": 0.065,
    "header_logo_size": (70, 70),
    "nav_icon_size": (30, 30),
    "button_padding_x": 20,
    "nav_font_size": 10,
    "corner_radius": 15,
    "frame1_icon_path": "assets/circuit.png",
    "frame1_icon_size": (390, 390),
    "frame1_icon_pos": (680, 180)
}