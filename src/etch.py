import serial
import time
import serial.tools.list_ports
import sys

def get_pico_port():
    # 1. Get a list of all available COM ports
    available_ports = serial.tools.list_ports.comports()
    
    if not available_ports:
        print("No COM ports detected. Is the Pico plugged in?")
        return None

    for port in available_ports:
        print(f"Checking: {port.device} - {port.description}")
        
        # 2. Filter: Only try ports that look like a Pico or USB Serial
        # Most grblHAL/Pico setups use these keywords in their description
        if "USB Serial" in port.description or "Pico" in port.description or "CH340" in port.description:
            try:
                # 3. Quick test connection
                test_s = serial.Serial(port.device, 115200, timeout=0.5)
                test_s.write(b"\r\n") # Wake it up
                time.sleep(1)
                test_s.close()
                return port.device # Success!
            except (serial.SerialException, PermissionError):
                continue # Port is busy or restricted
                
    return None

def etch_gcode(file_path, logger):
    # Helper to handle both GUI logging and terminal printing
    def log(msg):
        print(msg) # Still print to terminal for debugging
        if logger:
            logger(msg)

    # 1. Connect (Check your COM port in Device Manager!)
    try:
        pico_port = get_pico_port()
        if not pico_port:
            log("Error: No Pico W detected on any COM/TTY port.")
            return
            
        s = serial.Serial(pico_port, 115200, timeout=1)
    except Exception as e:
        log(f"Could not open port: {e}")
        return
    
    log("Initializing Pico...")
    s.write(b"\n")
    time.sleep(1)
    
    while s.in_waiting:
        s.readline() 

    log("Sending Unlock Command ($X)...")
    s.write(b"$X\n")
    
    success = False
    timeout = time.time() + 3
    while time.time() < timeout:
        if s.in_waiting:
            resp = s.readline().decode('utf-8').strip().lower()
            if 'ok' in resp:
                success = True
                log("Machine Unlocked and Ready.")
                break
    
    if not success:
        log("ALARM: Failed to unlock. Check limit switches!")
        return
    
    with open(file_path, 'r') as file:
        lines = file.readlines()
        total = len(lines)
        
        for i, line in enumerate(lines):
            l = line.strip()
            if not l or l.startswith('('): continue 
            
            s.write((l + '\n').encode('utf-8'))
            
            while True:
                response = s.readline().decode('utf-8').strip()
                if response == 'ok':
                    # Optional: Log every 10 lines to avoid spamming the GUI
                    if i % 10 == 0:
                        log(f"Progress: {i+1}/{total} lines")
                    break
                elif 'error' in response.lower():
                    log(f"!!! G-CODE ERROR at line {i+1}: {response}")
                    break
                elif 'ALARM' in response:
                    log(f"!!! HARD ALARM: {response}")
                    s.close()
                    return

    s.close()
    log("--- Etching Complete! ---")