#!/usr/bin/env python3
"""
Serial Communication Test for Camera Module
Tests communication with device on COM port
"""

import serial
import time
import sys

def test_serial_communication():
    """Test serial communication with the camera module"""
    
    # Try different common baud rates
    baud_rates = [115200, 9600, 57600, 38400, 19200]
    port = "COM5"  # Based on Device Manager
    
    print(f"Testing serial communication on {port}")
    print("=" * 50)
    
    for baud_rate in baud_rates:
        print(f"\nTrying baud rate: {baud_rate}")
        
        try:
            # Open serial connection
            ser = serial.Serial(port, baud_rate, timeout=2)
            time.sleep(2)  # Wait for connection to stabilize
            
            print(f"✅ Connected at {baud_rate} baud")
            
            # Clear any existing data
            ser.flushInput()
            ser.flushOutput()
            
            # Try sending some common commands
            commands = [
                b'\r\n',  # Just a newline
                b'AT\r\n',  # AT command
                b'help\r\n',  # Help command
                b'version\r\n',  # Version command
                b'camera\r\n',  # Camera command
                b'ls\r\n',  # List files (if Linux)
            ]
            
            for cmd in commands:
                print(f"Sending: {cmd.decode().strip()}")
                ser.write(cmd)
                time.sleep(1)
                
                # Read response
                response = b""
                while ser.in_waiting > 0:
                    response += ser.read(ser.in_waiting)
                    time.sleep(0.1)
                
                if response:
                    print(f"Response: {response.decode('utf-8', errors='ignore').strip()}")
                    
                    # If we got a meaningful response, try interactive mode
                    if len(response) > 5 and b'OK' in response or b'>' in response or b'$' in response:
                        print(f"\n🎉 Device responded! Entering interactive mode...")
                        print("Type commands below (type 'quit' to exit):")
                        
                        while True:
                            try:
                                user_input = input(">> ")
                                if user_input.lower() == 'quit':
                                    break
                                
                                ser.write((user_input + '\r\n').encode())
                                time.sleep(1)
                                
                                response = b""
                                while ser.in_waiting > 0:
                                    response += ser.read(ser.in_waiting)
                                    time.sleep(0.1)
                                
                                if response:
                                    print(response.decode('utf-8', errors='ignore'))
                                    
                            except KeyboardInterrupt:
                                break
                        
                        ser.close()
                        return True
            
            ser.close()
            print(f"❌ No meaningful response at {baud_rate} baud")
            
        except serial.SerialException as e:
            print(f"❌ Failed to connect at {baud_rate} baud: {e}")
        except Exception as e:
            print(f"❌ Error at {baud_rate} baud: {e}")
    
    print("\n❌ No successful communication found")
    print("\nTroubleshooting tips:")
    print("1. Try pressing RESET button on the device")
    print("2. Check if device needs different drivers")
    print("3. Device might need specific firmware flashed")
    return False

if __name__ == "__main__":
    # First install pyserial if needed
    try:
        import serial
    except ImportError:
        print("Installing pyserial...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyserial"])
        import serial
    
    test_serial_communication()