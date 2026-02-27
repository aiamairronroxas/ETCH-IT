# main.py
import tkinter as tk
from src.app_logic import EtchItApp

def main():
    root = tk.Tk()
    
    # Hide the window initially so it doesn't flash white during setup
    root.withdraw() 
    
    # Initialize the Application
    app = EtchItApp(root)
    
    # Force layout calculation
    root.update_idletasks()
    
    # Show the window once everything is drawn
    root.deiconify()
    
    root.mainloop()

if __name__ == "__main__":
    main()