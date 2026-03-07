import serial
import time
import os
from tkinter import messagebox

# --- CONFIGURATION ---
# SAFE_Z is still useful to ensure the bit lifts before moving to the start point
SAFE_Z = 2.0  

def etch_gcode(file_path, logger, pico_port):
    """
    pico_port: The COM/tty port identified during startup.
    """
    def log(msg):
        print(msg)
        if logger:
            logger(msg)

    # --- 1. OPEN SERIAL CONNECTION ---
    try:
        if not pico_port:
            log("Error: No Pico W port detected. Did the startup finish?")
            return
        
        # Open port (Homing and Probing are handled elsewhere)
        s = serial.Serial(pico_port, 115200, timeout=1)
    except Exception as e:
        log(f"Could not open port {pico_port}: {e}")
        return

    # Clear buffers
    log("Connecting to Pico...")
    s.write(b"\n")
    time.sleep(0.5)
    while s.in_waiting: s.readline() 

    # --- 2. ENSURE SAFE HEIGHT ---
    log(f"Lifting to Safe Height ({SAFE_Z}mm)...")
    # Sending G90 ensures the machine is in Absolute mode before moving
    s.write(f"G90\nG0 Z{SAFE_Z}\n".encode()) 
    
    # Wait for 'ok' to ensure the bit is actually up before the popup appears
    while True:
        line = s.readline().decode('utf-8').strip()
        if line == 'ok': 
            break

    s.write(b"$H\n") # This forces the machine to home automatically
    log("Homing machine to sync G10 offsets...")
    while True:
        if s.readline().decode('utf-8').strip() == 'ok': break

    # --- 3. SPINDLE START DIALOG ---
    # This pauses the script before any G-code is read
    log("Awaiting spindle start...")
    messagebox.showinfo("Start Spindle", 
        "The bit is at a safe height.\n\n"
        "1. Manually turn ON the drill spindle.\n"
        "2. Ensure any obstacles are clear.\n"
        "3. Click OK to begin etching.")

    # --- 4. STREAM G-CODE ---
    log(f"Streaming: {os.path.basename(file_path)}")
    
    with open(file_path, 'r') as file:
        for line in file:
            l = line.strip()
            
            # Skip empty lines and comments
            if not l or l.startswith('('): 
                continue 
            
            # Send line to Pico
            s.write((l + '\n').encode('utf-8'))
            
            # Wait for 'ok' before sending next line
            while True:
                response = s.readline().decode('utf-8').strip()
                if response == 'ok': 
                    break
                elif 'error' in response.lower() or 'ALARM' in response:
                    log(f"ALARM/ERROR: {response}")
                    log("Aborting Job.")
                    s.close()
                    return

    # --- 5. WAIT FOR PHYSICAL COMPLETION ---
    log("File sent. Waiting for machine to reach Idle state...")
    while True:
        s.write(b"?") # Query GRBL status
        time.sleep(0.3)
        if s.in_waiting:
            status = s.readline().decode('utf-8').strip()
            if 'Idle' in status:
                log("Machine finished moving.")
                break

    # --- 6. FINISH ---
    # Move back to origin after job? (Optional)
    # s.write(b"G0 X0 Y0\n")
    
    s.close() 
    log("--- Etching Process Complete ---")