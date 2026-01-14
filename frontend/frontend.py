import tkinter as tk
from tkinter import filedialog, messagebox
import os

class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ETCH-IT | PCB Manufacturing System")
        self.root.geometry("600x400")
        self.root.resizable(False, False)
        self.root.configure(bg="#1e1e1e")

        self.selected_mode = None

        self.create_home()

    def run(self):
        self.root.mainloop()

    # ==========================
    # HOME SCREEN
    # ==========================
    def create_home(self):
        self.clear_screen()

        title = tk.Label(
            self.root,
            text="ETCH-IT",
            font=("Segoe UI", 28, "bold"),
            fg="white",
            bg="#1e1e1e"
        )
        title.pack(pady=20)

        subtitle = tk.Label(
            self.root,
            text="Chemical-Free PCB Etching & Drilling System",
            font=("Segoe UI", 11),
            fg="#bbbbbb",
            bg="#1e1e1e"
        )
        subtitle.pack(pady=5)

        btn_frame = tk.Frame(self.root, bg="#1e1e1e")
        btn_frame.pack(pady=40)

        etch_btn = tk.Button(
            btn_frame,
            text="ETCH",
            font=("Segoe UI", 14),
            width=12,
            height=2,
            bg="#2d89ef",
            fg="white",
            command=lambda: self.select_mode("ETCH")
        )
        etch_btn.grid(row=0, column=0, padx=20)

        drill_btn = tk.Button(
            btn_frame,
            text="DRILL",
            font=("Segoe UI", 14),
            width=12,
            height=2,
            bg="#00a300",
            fg="white",
            command=lambda: self.select_mode("DRILL")
        )
        drill_btn.grid(row=0, column=1, padx=20)

    # ==========================
    # MODE SELECT
    # ==========================
    def select_mode(self, mode):
        self.selected_mode = mode
        self.open_file_dialog()

    # ==========================
    # FILE INPUT
    # ==========================
    def open_file_dialog(self):
        if self.selected_mode == "ETCH":
            filetypes = [("Gerber Files", "*.gbr")]
        else:
            filetypes = [("Drill Files", "*.xln *.drl")]

        filepath = filedialog.askopenfilename(
            title=f"Select {self.selected_mode} File",
            filetypes=filetypes
        )

        if filepath:
            messagebox.showinfo(
                "File Selected",
                f"{self.selected_mode} file loaded:\n\n{os.path.basename(filepath)}"
            )
            # Later: call backend here
        else:
            messagebox.showwarning("Cancelled", "No file selected.")

    # ==========================
    # UTIL
    # ==========================
    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()
