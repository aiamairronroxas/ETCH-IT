import serial
import serial.tools.list_ports
import time
import os
from tkinter import messagebox

# --- CONFIGURATION ---
SAFE_Z = 2.0  

def get_pico_port():
    """Scans for the Pico W or CH340 serial port."""
    available_ports = serial.tools.list_ports.comports()
    for port in available_ports:
        desc = port.description or ""
        dev = port.device or ""
        # Targets Raspberry Pi Pico, CH340, and Linux ttyACM devices
        if any(x in desc or x in dev for x in ["USB Serial", "Pico", "CH340", "ttyACM"]):
            try:
                # Test accessibility
                with serial.Serial(port.device, 115200, timeout=0.5) as test_s:
                    return port.device
            except (serial.SerialException, PermissionError):
                continue
    return None

def etch_gcode(file_path, logger=None):
    def log(msg):
        print(msg)
        if logger: logger(msg)

    pico_port = get_pico_port()
    if not pico_port:
        log("Error: No Pico W detected.")
        messagebox.showerror("Connection Error", "Pico W port not found.")
        return

    try:
        with serial.Serial(pico_port, 115200, timeout=1) as s:
            # --- INITIALIZE ---
            s.write(b"\r\n\r\n")
            time.sleep(1)
            s.reset_input_buffer() 

            log(f"Lifting to Safe Height ({SAFE_Z}mm)...")
            s.write(f"G90\nG0 Z{SAFE_Z}\n".encode()) 
            while 'ok' not in s.readline().decode('utf-8').strip(): pass

            # --- USER START ---
            messagebox.showinfo("Start Spindle", 
                                "1. Turn ON spindle.\n" \
                                "2. Click OK to start timer and etching.")

            # START TIMER
            start_time = time.time()
            log("Timer started.")

            # STREAM G-CODE
            with open(file_path, 'r') as file:
                for line in file:
                    clean_line = line.strip()
                    if not clean_line or clean_line.startswith('('): 
                        continue 
                    
                    # Send line to Pico
                    s.write((clean_line + '\n').encode('utf-8'))
                    
                    # Wait for Pico to acknowledge (the 'ok' response)
                    while True:
                        res = s.readline().decode('utf-8').strip()
                        if 'ok' in res: 
                            break
                        elif 'error' in res.lower() or 'ALARM' in res:
                            log(f"CRITICAL ERROR: {res}")
                            return

            # --- WAIT FOR IDLE (The "Busy" Check) ---
            log("Job streamed. Waiting for physical completion...")
            while True:
                s.write(b"?") 
                status = s.readline().decode('utf-8')
                if 'Idle' in status:
                    break
                time.sleep(0.5) # Poll every half second to keep serial traffic low

            # STOP TIMER
            end_time = time.time()
            duration = end_time - start_time
            log(f"Job finished in {duration:.2f} seconds.")

            # --- FILE PERSISTENCE LOGIC ---

            script_dir = os.path.dirname(os.path.abspath(__file__))
            count_file = os.path.join(script_dir, "count.txt")
            current_total = 0.0

            # 1. Read existing value
            if os.path.exists(count_file):
                with open(count_file, 'r') as f:
                    content = f.read().strip()
                    if content:
                        try:
                            current_total = float(content)
                        except ValueError:
                            current_total = 0.0
            
            # 2. Add duration and save
            new_total = current_total + duration
            with open(count_file, 'w') as f:
                f.write(f"{new_total:.2f}")
                f.flush()            # Pushes data out of Python
                os.fsync(f.fileno()) # Pushes data to the physical disk

            log(f"Total cumulative time in count.txt: {new_total:.2f} seconds.")

            try:
                #from backup.maintenance import check_machine_runtime   # USE ONLY ON RPI 4B
                #check_machine_runtime()                                # This updates the LED based on the new total
                print("wow")
            except Exception as e:
                log(f"Maintenance Check Error: {e}")

    except Exception as e:
        log(f"Error: {e}")

    log("--- Process Complete ---")