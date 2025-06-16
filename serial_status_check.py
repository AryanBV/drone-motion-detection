#!/usr/bin/env python3
"""
ESP32-CAM Serial Status Checker
Check current status and see what services are running
"""

import serial
import time
import re

def check_esp32_status():
    """Check ESP32-CAM current status via serial"""
    print("🔌 Connecting to ESP32-CAM via serial...")
    
    try:
        ser = serial.Serial("COM5", 115200, timeout=3)
        time.sleep(2)
        print("✅ Serial connected")
        
        # Clear buffer first
        ser.flushInput()
        ser.flushOutput()
        
        print("\n📊 Getting ESP32-CAM status...")
        
        # Send various status commands
        commands = [
            ("", "Basic connection test"),
            ("help", "Available commands"),
            ("status", "System status"),
            ("ip", "IP information"),
            ("wifi", "WiFi status"),
            ("AT+CIFSR", "Get IP address"),
            ("AT+CWJAP?", "Current WiFi connection"),
            ("web", "Web server status"),
            ("cam", "Camera status"),
            ("server", "Server status"),
            ("info", "Device information"),
            ("version", "Firmware version"),
        ]
        
        responses = {}
        
        for cmd, description in commands:
            print(f"\n🔍 Testing: {description}")
            print(f"📤 Sending: '{cmd}'")
            
            # Clear buffers
            ser.flushInput()
            ser.flushOutput()
            
            # Send command
            ser.write((cmd + '\r\n').encode())
            time.sleep(2)
            
            # Read response
            response = ""
            start_time = time.time()
            while time.time() - start_time < 3:
                if ser.in_waiting > 0:
                    response += ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                time.sleep(0.1)
            
            if response.strip():
                print(f"📥 Response: {response.strip()}")
                responses[cmd] = response.strip()
                
                # Look for IP addresses
                ip_pattern = r'(\d+\.\d+\.\d+\.\d+)'
                ips = re.findall(ip_pattern, response)
                if ips:
                    print(f"🎯 Found IPs in response: {ips}")
                
                # Look for web server indicators
                web_indicators = ['http', 'server', 'port', '80', 'web', 'camera']
                found_indicators = [ind for ind in web_indicators if ind.lower() in response.lower()]
                if found_indicators:
                    print(f"🌐 Web indicators: {found_indicators}")
            else:
                print("📥 No response")
        
        # Check for continuous output (like log messages)
        print(f"\n📡 Listening for continuous output for 10 seconds...")
        start_time = time.time()
        continuous_output = ""
        
        while time.time() - start_time < 10:
            if ser.in_waiting > 0:
                new_data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                continuous_output += new_data
                print(f"📨 Live: {new_data.strip()}")
            time.sleep(0.5)
        
        ser.close()
        
        # Analyze results
        print(f"\n" + "="*50)
        print(f"📊 ANALYSIS RESULTS")
        print(f"="*50)
        
        # Check for IP addresses in all responses
        all_responses = " ".join(responses.values()) + " " + continuous_output
        all_ips = re.findall(r'(\d+\.\d+\.\d+\.\d+)', all_responses)
        unique_ips = list(set(all_ips))
        
        if unique_ips:
            print(f"🎯 Found IP addresses: {unique_ips}")
            for ip in unique_ips:
                if ip.startswith('192.168.195.'):
                    print(f"   ✅ Hotspot IP: {ip}")
                else:
                    print(f"   ℹ️  Other IP: {ip}")
        else:
            print(f"❌ No IP addresses found in responses")
        
        # Check for web server indicators
        web_keywords = ['http', 'server', 'web', 'port 80', ':80', 'mjpeg', 'stream']
        found_web = [kw for kw in web_keywords if kw.lower() in all_responses.lower()]
        
        if found_web:
            print(f"🌐 Web server indicators found: {found_web}")
        else:
            print(f"❌ No web server indicators found")
            print(f"⚠️  This firmware might not have a web server!")
        
        # Check for camera indicators
        camera_keywords = ['camera', 'cam', 'jpeg', 'mjpeg', 'capture', 'stream']
        found_camera = [kw for kw in camera_keywords if kw.lower() in all_responses.lower()]
        
        if found_camera:
            print(f"📷 Camera indicators found: {found_camera}")
        else:
            print(f"❌ No camera indicators found")
        
        return responses, unique_ips
        
    except Exception as e:
        print(f"❌ Serial check failed: {e}")
        return None, None

def recommend_solutions(responses, ips):
    """Recommend solutions based on findings"""
    print(f"\n🔧 RECOMMENDATIONS:")
    print(f"="*50)
    
    if not responses:
        print(f"1. ❌ Cannot communicate with ESP32-CAM")
        print(f"   - Check USB connection")
        print(f"   - Try different COM port")
        print(f"   - Check if device is in programming mode")
        return
    
    if not ips:
        print(f"1. ❌ ESP32-CAM not connected to WiFi properly")
        print(f"   - Power cycle the device")
        print(f"   - Re-run WiFi configuration")
        print(f"   - Check hotspot password")
        return
    
    # Check if web server keywords found
    all_text = " ".join(responses.values()).lower()
    if 'http' not in all_text and 'server' not in all_text and 'web' not in all_text:
        print(f"1. ⚠️  FIRMWARE ISSUE: No web server detected!")
        print(f"   - This firmware might not have a web server")
        print(f"   - Need to flash ESP32-CAM with MJPEG2SD firmware")
        print(f"   - Or try different firmware with web interface")
        print(f"")
        print(f"2. 🔧 To fix this:")
        print(f"   - Download MJPEG2SD firmware")
        print(f"   - Flash it to ESP32-CAM using Arduino IDE")
        print(f"   - Or try CameraWebServer example from Arduino")
        return
    
    if ips:
        hotspot_ips = [ip for ip in ips if ip.startswith('192.168.195.')]
        if hotspot_ips:
            print(f"1. ✅ ESP32-CAM connected with IP: {hotspot_ips[0]}")
            print(f"   - Try: http://{hotspot_ips[0]}")
            print(f"   - Try: http://{hotspot_ips[0]}:8080")
            print(f"   - Try: http://{hotspot_ips[0]}/cam-hi.jpg")
        else:
            print(f"1. ⚠️  ESP32-CAM has IP but not on hotspot network")
            print(f"   - Found IPs: {ips}")
            print(f"   - Might be connected to different network")

def main():
    print("🔌 ESP32-CAM Serial Status Checker")
    print("="*50)
    print("📋 This will check what's running on your ESP32-CAM")
    print("")
    
    responses, ips = check_esp32_status()
    recommend_solutions(responses, ips)
    
    print(f"\n💡 Next Steps:")
    print(f"1. Check your phone's hotspot connected devices")
    print(f"2. If ESP32-CAM is connected but no web server:")
    print(f"   - The firmware needs to be changed")
    print(f"   - Need firmware with built-in web server")
    print(f"3. If you see the correct IP, try browser again")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Interrupted")
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"Make sure ESP32-CAM is connected via USB to COM5")