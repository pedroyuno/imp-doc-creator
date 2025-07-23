#!/usr/bin/env python3
"""
Utility to check which ports are in use
"""

import socket
import subprocess
import sys

def check_port(port):
    """Check if a port is in use."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', port))
            return False  # Port is free
    except OSError:
        return True  # Port is in use

def find_process_on_port(port):
    """Find what process is using a port (macOS/Linux)."""
    try:
        result = subprocess.run(['lsof', '-ti', f':{port}'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            pid = result.stdout.strip()
            if pid:
                # Get process name
                proc_result = subprocess.run(['ps', '-p', pid, '-o', 'comm='], 
                                           capture_output=True, text=True)
                if proc_result.returncode == 0:
                    return f"PID {pid} ({proc_result.stdout.strip()})"
        return "Unknown process"
    except:
        return "Unable to determine"

def main():
    print("🔍 Port Usage Check")
    print("=" * 30)
    
    ports_to_check = [5000, 5001, 5002, 5003, 8000, 8080]
    
    for port in ports_to_check:
        if check_port(port):
            process = find_process_on_port(port)
            print(f"Port {port}: ❌ IN USE ({process})")
        else:
            print(f"Port {port}: ✅ Available")
    
    print("\n💡 Note: Port 5000 is often used by macOS AirPlay Receiver")
    print("   You can disable it in: System Preferences → Sharing → AirPlay Receiver")

if __name__ == "__main__":
    main() 