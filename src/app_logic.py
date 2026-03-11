import tkinter as tk
from tkinter import font, filedialog, messagebox
from PIL import Image, ImageTk
from datetime import datetime
import os
import threading


# Import your existing backend functions
from src.drill import plot_excellon
from src.drill_gcode import generate_drill_gcode
from src.mill import plot_gerber
from src.mill_gcode import generate_mill_gcode
from src.etch import etch_gcode
from src.maintenance import check_machine_runtime  #USE THIS ONLY ON PI 4B

from .config import COLORS, FRAME_CONFIGS, APP_SETTINGS
from .utils import draw_rounded_rect, apply_dark_title_bar

class EtchItApp:
    def __init__(self, root):
        self.root = root
        self.root.title("ETCH-IT")
        
        # --- Fullscreen & Resize Settings ---
        self.root.attributes('-fullscreen', True)
        self.root.resizable(False, False)
        self.root.bind("<Escape>", lambda e: self.root.destroy())

        # Load configs
        self.colors = COLORS
        self.cfg = APP_SETTINGS
        self.f2_cfg = FRAME_CONFIGS["f2_btn"]
        self.f3_cfg = FRAME_CONFIGS["f3_btn"]
        self.status_cfg = FRAME_CONFIGS["status"]
        self.right_standalone_cfg = FRAME_CONFIGS["standalone_icon"]

        apply_dark_title_bar(self.root)
        self.root.configure(bg=self.colors["root_bg"])
        self.load_assets()

        # --- Layout Setup ---
        self.sidebar = tk.Frame(self.root, bg=self.colors["sidebar_bg"])
        self.sidebar.place(relx=0, rely=0, relwidth=self.cfg["sidebar_rel_width"], relheight=1)

        self.main_content = tk.Frame(self.root, bg=self.colors["main_content_bg"])
        self.main_content.place(relx=self.cfg["sidebar_rel_width"], rely=0, 
                                relwidth=1-self.cfg["sidebar_rel_width"], relheight=1)

        # --- HOMEPAGE ELEMENTS ---
        self.home_elements = []
        self.anim_x, self.anim_y = 90, 60
        self.welcome_label = tk.Label(self.main_content, text="", bg=self.colors["main_content_bg"], 
                                      fg=self.colors["accent_red"], font=("Arial", 20, "bold"))
        self.welcome_label.place(x=self.anim_x, y=self.anim_y)
        self.home_elements.append(self.welcome_label)
        
        self.subtitle_label = tk.Label(self.main_content, text="PCB Etching and Drilling Device for Chemical-Free Fabrication", 
                                      bg=self.colors["main_content_bg"], fg=self.colors["text_secondary"], font=("Arial", 16))
        self.subtitle_label.place(x=90, y=95)
        self.home_elements.append(self.subtitle_label)

        # --- FRAME 1 (Generate Section) ---
        self.center_frame_x, self.center_frame_y = 90, 160
        self.center_frame_w, self.center_frame_h = 900, 410
        self.mid_canvas = tk.Canvas(self.main_content, bg=self.colors["main_content_bg"], highlightthickness=0)
        self.mid_canvas.place(x=self.center_frame_x, y=self.center_frame_y, width=self.center_frame_w, height=self.center_frame_h)
        self.home_elements.append(self.mid_canvas)
        self.draw_f1_content()

        # --- FRAME 2 (View Button) ---
        f2 = self.f2_cfg
        self.mid_canvas2 = tk.Canvas(self.main_content, bg=self.colors["main_content_bg"], 
                                     width=f2["width"], height=f2["height"], highlightthickness=0, cursor="hand2")
        self.mid_canvas2.place(x=f2["pos_x"], y=f2["pos_y"])
        self.home_elements.append(self.mid_canvas2)
        self.draw_f2_button()

        # --- FRAME 3 (Etch-IT! Button) ---
        f3 = self.f3_cfg
        self.mid_canvas3 = tk.Canvas(self.main_content, bg=self.colors["main_content_bg"], 
                                     width=f3["width"], height=f3["height"], highlightthickness=0, cursor="hand2")
        self.mid_canvas3.place(x=f3["pos_x"], y=f3["pos_y"])
        self.home_elements.append(self.mid_canvas3)
        self.draw_f3_button()

        # --- STATUS CONSOLE ---
        self.setup_status_console()

        # --- STANDALONE ICON ---
        if hasattr(self, 'right_standalone_img'):
            self.standalone_icon_label = tk.Label(self.main_content, image=self.right_standalone_img, 
                                                  bg=self.colors["main_content_bg"])
            self.standalone_icon_label.place(x=self.right_standalone_cfg["pos_x"], 
                                            y=self.right_standalone_cfg["pos_y"])
            self.home_elements.append(self.standalone_icon_label)

        self.active_serial = None    # SERIAL TERMINAL
        # Sidebar setup
        self.setup_header("assets/logo2.png")
        self.home_btn = self.create_nav_item("Home", self.home_icon_img, pack_side="top")
        self.stop_btn = self.create_nav_item("STOP", self.emergency_icon_img, pack_side="top")
        self.exit_btn = self.create_nav_item("Exit", self.exit_icon_img, pack_side="bottom")
        self.hide_btn = self.create_nav_item("Hide", self.hide_icon_img, pack_side="bottom")
        
        self.phrases = ["Welcome to ETCH-IT!", "Interprets Gerber Files", "Generates G-codes!"]
        self.current_phrase_index = 0
        self.typewriter_effect(0)
        self.root.after(100, self.sync_sidebar_buttons)
        
        self.log_message("System Initialized... Ready for input.")
        self.root.after(3500, lambda: check_machine_runtime(logger=self.log_message))              # RUN THIS ONLY ON RPI 4B
    # --- CORE LOGIC HELPER ---
    def get_file_and_mode(self):
        filetypes = [
            ("PCB Files", "*.gbr *.xln *.drl"),
            ("Gerber (Etch)", "*.gbr"),
            ("Excellon (Drill)", "*.xln *.drl")
        ]
        filepath = filedialog.askopenfilename(title="Open PCB File", filetypes=filetypes)
        if not filepath: return None, None
        
        ext = os.path.splitext(filepath)[1].lower()
        mode = "ETCH" if ext == ".gbr" else "DRILL" if ext in [".xln", ".drl"] else None
        
        if not mode:
            messagebox.showerror("Error", "Unsupported file format.")
            return None, None
        return filepath, mode

    # --- BUTTON ACTIONS ---
    def on_view_click(self, event=None):
        """Logic for the 'View Gerber' button."""
        filepath, mode = self.get_file_and_mode()
        if not filepath: return

        self.log_message(f"Viewing {mode} file: {os.path.basename(filepath)}")
        try:
            if mode == "ETCH":
                plot_gerber(filepath)
            else:
                plot_excellon(filepath)
        except Exception as e:
            self.log_message(f"VIEW ERROR: {str(e)}")
            messagebox.showerror("View Error", str(e))

    def on_generate_click(self, event=None):
        """Logic for the 'GENERATE!' button."""
        filepath, mode = self.get_file_and_mode()
        if not filepath: return

        base_name = os.path.splitext(os.path.basename(filepath))[0]
        output_nc = filedialog.asksaveasfilename(
            title=f"Save {mode} G-Code",
            initialfile=f"{base_name}_{mode.lower()}.nc",
            defaultextension=".nc",
            filetypes=[("G-Code Files", "*.nc")]
        )

        if not output_nc: return

        # Log start of process locally in the UI
        self.log_message(f"--- Starting {mode} Generation ---")
        
        try:
            if mode == "ETCH":
                # Pass self.log_message so generate_mill_gcode can talk to your UI
                # tool_dia is hardcoded to 0.2 inside or passed here
                success = generate_mill_gcode(
                    filepath, 
                    logger=self.log_message, 
                    output_file=output_nc,
                    tool_dia=0.2
                )
            else:
                # If you update generate_drill_gcode later, add logger=self.log_message there too
                mode = "DRILL"
                success = generate_drill_gcode(filepath, output_file=output_nc)

            if success:
                self.log_message(f"FILE SAVED: {os.path.basename(output_nc)}")
                messagebox.showinfo("Success", f"{mode} G-Code saved successfully!")
            else:
                # If success is False, the collision error has already been printed to your logs
                messagebox.showwarning("Generation Failed", "Collision detected or file error. Check logs.")

        except Exception as e:
            self.log_message(f"CRITICAL GEN ERROR: {str(e)}")
            messagebox.showerror("Error", f"An unexpected error occurred: {str(e)}")

    # --- PLACE ETCH FUNCTION HERE ---

    def on_etch_click(self, event=None):
        file_path = filedialog.askopenfilename(filetypes=[("G-Code Files", "*.nc *.gcode"), ("All Files", "*.*")])
        if not file_path: return

        # We wrap the etch_gcode in a thread
        # This lets the function run in the background 
        # while the Tkinter GUI stays "alive" and interactive.
        etch_thread = threading.Thread(target=self.run_background_etch, args=(file_path,))
        etch_thread.daemon = True  # If you close the app, the thread closes too
        etch_thread.start()

    def run_background_etch(self, file_path):
        # This runs in the background
        etch_gcode(file_path, logger=self.log_message, app_reference=self)

    # --- UI DRAWING METHODS ---
    def draw_f1_content(self):
        self.mid_canvas.delete("all")
        draw_rounded_rect(self.mid_canvas, 0, 0, self.center_frame_w, self.center_frame_h, 20, 
                          gradient=(self.colors["f1_grad_start"], self.colors["f1_grad_end"]))
        self.mid_canvas.create_text(70, 110, text="Generate G-Code", fill="#FFFFFF", font=("Arial", 30, "bold"), anchor="w")
        self.mid_canvas.create_text(72, 150, text="Direct conversion to NC file", fill="#FFFFFF", font=("Arial", 14), anchor="w")
        
        if hasattr(self, 'frame1_right_icon'):
            pos = self.cfg["frame1_icon_pos"]
            self.mid_canvas.create_image(pos[0], pos[1] + 20, image=self.frame1_right_icon)
        
        self.start_btn_canvas = tk.Canvas(self.mid_canvas, bg=self.colors["f1_grad_start"], width=220, height=50, highlightthickness=0, cursor="hand2")
        self.start_btn_canvas.place(x=130, y=240)

        def draw_gen_btn(color):
            draw_rounded_rect(self.start_btn_canvas, 0, 0, 220, 50, 10, color=color)
            self.start_btn_canvas.create_text(110, 25, text="GENERATE!", fill=self.colors["btn_text_white"], font=("Arial", 10, "bold"))
        
        draw_gen_btn("#424242")
        self.start_btn_canvas.bind("<Enter>", lambda e: draw_gen_btn("#5a5a5a"))
        self.start_btn_canvas.bind("<Leave>", lambda e: draw_gen_btn("#424242"))
        self.start_btn_canvas.bind("<Button-1>", self.on_generate_click)

    def draw_f2_button(self, hover=False):
        self.mid_canvas2.delete("all")
        f = self.f2_cfg
        c1 = self.colors["f2_hover_start"] if hover else self.colors["f2_grad_start"]
        c2 = self.colors["f2_hover_end"] if hover else self.colors["f2_grad_end"]
        
        draw_rounded_rect(self.mid_canvas2, 0, 0, f["width"], f["height"], f["corner_radius"], gradient=(c1, c2))
        
        text_font = font.Font(family=f["font"][0], size=f["font"][1], weight=f["font"][2])
        total_w = f["icon_size"][0] + f["spacing"] + text_font.measure(f["text"])
        start_x = (f["width"] - total_w) / 2
        
        if hasattr(self, 'f2_icon_img'):
            self.mid_canvas2.create_image(start_x + (f["icon_size"][0]/2), f["height"]/2, image=self.f2_icon_img)
        self.mid_canvas2.create_text(start_x + f["icon_size"][0] + f["spacing"], f["height"]/2, text=f["text"], fill=f["text_color"], font=f["font"], anchor="w")
        self.mid_canvas2.bind("<Button-1>", self.on_view_click)
        self.mid_canvas2.bind("<Enter>", lambda e: self.draw_f2_button(hover=True))
        self.mid_canvas2.bind("<Leave>", lambda e: self.draw_f2_button(hover=False))

    def draw_f3_button(self, hover=False):
        self.mid_canvas3.delete("all")
        f = self.f3_cfg
        c1 = self.colors["f3_hover_start"] if hover else self.colors["f3_grad_start"]
        c2 = self.colors["f3_hover_end"] if hover else self.colors["f3_grad_end"]
        
        draw_rounded_rect(self.mid_canvas3, 0, 0, f["width"], f["height"], f["corner_radius"], gradient=(c1, c2))
        
        text_font = font.Font(family=f["font"][0], size=f["font"][1], weight=f["font"][2])
        total_w = f["icon_size"][0] + f["spacing"] + text_font.measure(f["text"])
        start_x = (f["width"] - total_w) / 2
        
        if hasattr(self, 'f3_icon_img'):
            self.mid_canvas3.create_image(start_x + (f["icon_size"][0]/2), f["height"]/2, image=self.f3_icon_img)
        self.mid_canvas3.create_text(start_x + f["icon_size"][0] + f["spacing"], f["height"]/2, text=f["text"], fill=f["text_color"], font=f["font"], anchor="w")
        self.mid_canvas3.bind("<Button-1>", self.on_etch_click)
        self.mid_canvas3.bind("<Enter>", lambda e: self.draw_f3_button(hover=True))
        self.mid_canvas3.bind("<Leave>", lambda e: self.draw_f3_button(hover=False))

    # --- REST OF CLASS (ASSETS, LOGS, NAV) ---
    def load_assets(self):
        try:
            self.home_icon_img = ImageTk.PhotoImage(Image.open("assets/home.png").resize(self.cfg["nav_icon_size"], Image.Resampling.LANCZOS))
            self.exit_icon_img = ImageTk.PhotoImage(Image.open("assets/logo3.png").resize(self.cfg["nav_icon_size"], Image.Resampling.LANCZOS))
            self.hide_icon_img = ImageTk.PhotoImage(Image.open("assets/logo4.png").resize(self.cfg["nav_icon_size"], Image.Resampling.LANCZOS))
            self.emergency_icon_img = ImageTk.PhotoImage(Image.open("assets/emergency.png").resize(self.cfg["nav_icon_size"], Image.Resampling.LANCZOS))

            f1_icon = Image.open(self.cfg["frame1_icon_path"]).resize(self.cfg["frame1_icon_size"], Image.Resampling.LANCZOS)
            self.frame1_right_icon = ImageTk.PhotoImage(f1_icon)
            f2_icon = Image.open(self.f2_cfg["icon_path"]).resize(self.f2_cfg["icon_size"], Image.Resampling.LANCZOS)
            self.f2_icon_img = ImageTk.PhotoImage(f2_icon)
            f3_icon = Image.open(self.f3_cfg["icon_path"]).resize(self.f3_cfg["icon_size"], Image.Resampling.LANCZOS)
            self.f3_icon_img = ImageTk.PhotoImage(f3_icon)
            standalone_img = Image.open(self.right_standalone_cfg["path"]).resize(self.right_standalone_cfg["size"], Image.Resampling.LANCZOS)
            self.right_standalone_img = ImageTk.PhotoImage(standalone_img)
        except Exception as e:
            print(f"Asset Error: {e}")

    def setup_status_console(self):
        s = self.status_cfg
        self.console_canvas = tk.Canvas(self.main_content, bg=self.colors["main_content_bg"], width=s["width"], height=s["height"], highlightthickness=0)
        self.console_canvas.place(x=s["pos_x"], y=s["pos_y"])
        draw_rounded_rect(self.console_canvas, 0, 0, s["width"], s["height"], s["corner_radius"], color=self.colors["console_bg"])
        self.console_canvas.create_text(20, 30, text="SYSTEM LOGS", fill=self.colors["accent_red"], font=("Arial", 14, "bold"), anchor="w")
        self.console_canvas.create_line(20, 50, s["width"]-20, 50, fill="#EEEEEE")
        self.log_widget = tk.Text(self.main_content, bg=self.colors["console_bg"], fg=self.colors["text_primary"], font=("Consolas", 10), borderwidth=0, highlightthickness=0, state='disabled')
        self.log_widget.place(x=s["pos_x"]+15, y=s["pos_y"]+60, width=s["width"]-30, height=s["height"]-80)

    def log_message(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_widget.config(state='normal')
        self.log_widget.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_widget.see(tk.END)
        self.log_widget.config(state='disabled')

    def create_nav_item(self, text, icon, pack_side="top"):
        canvas = tk.Canvas(self.sidebar, bg=self.colors["sidebar_bg"], highlightthickness=0, cursor="hand2")
        canvas.pack(side=pack_side, padx=self.cfg["button_padding_x"], pady=(10, 20 if text == "Exit" else 0))
        canvas.bind("<Enter>", lambda e: self.draw_btn(canvas, self.colors["nav_hover"], text, icon))
        canvas.bind("<Leave>", lambda e: self.draw_btn(canvas, self.colors["sidebar_bg"], text, icon))
        canvas.bind("<Button-1>", lambda e: self.handle_click(text))
        return {"canvas": canvas, "text": text, "icon": icon}

    def draw_btn(self, canvas, color, text, icon):
        canvas.delete("all")
        canvas.update_idletasks()
        w, h = canvas.winfo_width(), canvas.winfo_height()
        if w < 5: return
        draw_rounded_rect(canvas, 0, 0, w, h, self.cfg["corner_radius"], color=color)
        if icon: canvas.create_image(w/2, h/2 - 10, image=icon)
        canvas.create_text(w/2, h/2 + (18 if icon else 0), text=text, fill=self.colors["sidebar_text"], font=("Arial", self.cfg["nav_font_size"], "bold"))

    def handle_click(self, name):
        if name == "Exit": self.root.destroy()
        elif name == "Hide": self.root.iconify()
        elif name == "STOP": self.handle_emergency_stop()

    def setup_header(self, logo_path):
        try:
            img = Image.open(logo_path).resize(self.cfg["header_logo_size"], Image.Resampling.LANCZOS)
            self.side_logo_img = ImageTk.PhotoImage(img)
            tk.Label(self.sidebar, image=self.side_logo_img, bg=self.colors["sidebar_bg"]).pack(pady=(40, 5)) 
            tk.Label(self.sidebar, text="ETCH-IT", bg=self.colors["sidebar_bg"], fg=self.colors["sidebar_text"], font=("Arial", 11, "bold")).pack(pady=(0, 30))
        except: pass

    def typewriter_effect(self, char_index):
        phrase = self.phrases[self.current_phrase_index]
        if char_index <= len(phrase):
            self.welcome_label.config(text=phrase[:char_index])
            self.root.after(100, lambda: self.typewriter_effect(char_index + 1))
        else: self.root.after(500, lambda: self.jump_animation(0, 2))

    def jump_animation(self, jump_count, total_jumps):
        if jump_count < total_jumps:
            self.welcome_label.place(x=self.anim_x, y=self.anim_y - 15)
            self.root.after(150, lambda: self.welcome_label.place(x=self.anim_x, y=self.anim_y))
            self.root.after(300, lambda: self.jump_animation(jump_count + 1, total_jumps))
        else: self.root.after(1500, self.next_phrase)

    def next_phrase(self):
        self.current_phrase_index = (self.current_phrase_index + 1) % len(self.phrases)
        self.welcome_label.config(text="")
        self.typewriter_effect(0)

    def sync_sidebar_buttons(self, event=None):
        self.sidebar.update_idletasks()
        sidebar_w = self.sidebar.winfo_width()
        new_size = sidebar_w - (self.cfg["button_padding_x"] * 2)
        if new_size > 20:
            for btn in [self.home_btn, self.stop_btn, self.exit_btn, self.hide_btn]:
                btn["canvas"].config(width=new_size, height=new_size)
                self.root.after(10, lambda b=btn: self.draw_btn(b["canvas"], self.colors["sidebar_bg"], b["text"], b["icon"]))

    def clear_screen(self):
        for widget in self.main_content.winfo_children():
            widget.destroy()

    def handle_emergency_stop(self):
        if self.active_serial and self.active_serial.is_open:
            try:
                # 1. Clear the Python-side buffer
                self.active_serial.reset_output_buffer()
                
                # 2. Send the Soft Reset character (0x18)
                # This is the standard "Abort" for GRBL/CNC controllers
                self.active_serial.write(b'\x18') 
                self.log_message("!!! EMERGENCY STOP !!!")
                self.log_message("Abort signal (0x18) sent to Pico.")
            except Exception as e:  
                self.log_message(f"Stop Failed: {e}")
        else:
            self.log_message("No active serial connection to stop.")