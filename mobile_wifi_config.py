#!/usr/bin/env python3
"""
ESP32-CAM Mobile Hotspot Configuration Tool
Configure ESP32-CAM to connect to your mobile phone's hotspot
"""

import serial
import time
import socket
import requests
from concurrent.futures import ThreadPoolExecutor

class MobileHotspotConfig:
    def __init__(self, port="COM5", baudrate=115200):
        self.port = port
        self.baudrate = baudrate
        self.ser = None
    
    def connect_serial(self):
        """Connect to ESP32-CAM via serial"""
        print(f"🔌 Connecting to {self.port} at {self.baudrate} baud...")
        
        try:
            self.ser = serial.Serial(self.port, self.baudrate, timeout=2)
            time.sleep(2)  # Wait for connection
            print("✅ Serial connection established")
            return True
        except Exception as e:
            print(f"❌ Serial connection failed: {e}")
            return False
    
    def send_command(self, command, wait_time=2):
        """Send command and read response"""
        if not self.ser:
            return None
        
        try:
            # Clear buffer
            self.ser.flushInput()
            self.ser.flushOutput()
            
            # Send command
            cmd_bytes = (command + '\r\n').encode()
            self.ser.write(cmd_bytes)
            print(f"📤 Sent: {command}")
            
            # Wait for response
            time.sleep(wait_time)
            
            # Read response
            response = ""
            while self.ser.in_waiting > 0:
                response += self.ser.read(self.ser.in_waiting).decode('utf-8', errors='ignore')
                time.sleep(0.1)
            
            if response.strip():
                print(f"📥 Response: {response.strip()}")
            
            return response
            
        except Exception as e:
            print(f"❌ Command failed: {e}")
            return None
    
    def configure_mobile_wifi(self, ssid, password):
        """Configure WiFi for mobile hotspot"""
        print(f"\n📶 Configuring WiFi: {ssid}")
        
        # Try different command formats for ESP32-CAM
        wifi_commands = [
            f"wifi_config {ssid} {password}",
            f"setWiFi {ssid} {password}",
            f"AT+CWJAP=\"{ssid}\",\"{password}\"",
            f"wifi.config('{ssid}','{password}')",
            f"connect {ssid} {password}",
            f"wifiConnect {ssid} {password}",
            f"setupWiFi {ssid} {password}",
        ]
        
        for cmd in wifi_commands:
            print(f"\n🔧 Trying: {cmd}")
            response = self.send_command(cmd, 5)
            
            if response and any(keyword in response.lower() for keyword in 
                              ['ok', 'connected', 'success', 'wifi connected', 'saved']):
                print("✅ WiFi configuration command sent successfully!")
                return True
        
        print("⚠️ No clear success response. WiFi might still be configured.")
        return False
    
    def restart_device(self):
        """Restart the ESP32-CAM"""
        print("\n🔄 Restarting ESP32-CAM...")
        
        restart_commands = [
            "restart",
            "reboot",
            "reset",
            "AT+RST",
            "ESP.restart()",
            "system.restart()",
        ]
        
        for cmd in restart_commands:
            response = self.send_command(cmd, 2)
            if response:
                break
        
        print("⏳ Waiting for restart...")
        time.sleep(10)
    
    def scan_for_esp32_on_hotspot(self):
        """Scan for ESP32-CAM on mobile hotspot network"""
        print("\n🔍 Scanning for ESP32-CAM on your mobile hotspot...")
        
        # Common mobile hotspot IP ranges
        hotspot_ranges = [
            "192.168.43.",   # Android hotspot default
            "172.20.10.",    # iPhone hotspot default
            "192.168.137.",  # Windows hotspot
            "10.0.0.",       # Some mobile hotspots
        ]
        
        # Get current IP to determine which range we're on
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            
            current_range = '.'.join(local_ip.split('.')[:-1]) + '.'
            if current_range not in hotspot_ranges:
                hotspot_ranges.insert(0, current_range)
            
            print(f"📱 Your current IP: {local_ip}")
            print(f"🔍 Scanning ranges: {hotspot_ranges}")
            
        except:
            print("📱 Using default mobile hotspot ranges")
        
        def check_ip(ip):
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(1)
                result = sock.connect_ex((ip, 80))
                sock.close()
                if result == 0:
                    return ip
            except:
                pass
            return None
        
        found_ips = []
        
        for ip_range in hotspot_ranges:
            print(f"📡 Scanning {ip_range}1-254...")
            
            with ThreadPoolExecutor(max_workers=50) as executor:
                futures = [executor.submit(check_ip, f"{ip_range}{i}") for i in range(1, 255)]
                
                for future in futures:
                    result = future.result()
                    if result and result != local_ip:
                        found_ips.append(result)
                        print(f"✅ Found web server: {result}")
        
        # Test which ones are ESP32-CAM
        esp32_ips = []
        for ip in found_ips:
            if self.test_esp32_cam(ip):
                esp32_ips.append(ip)
        
        return esp32_ips
    
    def test_esp32_cam(self, ip):
        """Test if IP is ESP32-CAM"""
        try:
            response = requests.get(f"http://{ip}", timeout=3)
            if response.status_code == 200:
                content = response.text.lower()
                esp32_indicators = ['esp32', 'camera', 'stream', 'capture', 'mjpeg']
                
                if any(indicator in content for indicator in esp32_indicators):
                    print(f"🎥 ESP32-CAM confirmed at: {ip}")
                    return True
        except:
            pass
        return False
    
    def close(self):
        """Close serial connection"""
        if self.ser:
            self.ser.close()

def main():
    print("📱 ESP32-CAM Mobile Hotspot Configuration")
    print("=" * 60)
    
    # Step 1: Get mobile hotspot info
    print("📱 First, set up your mobile hotspot:")
    print("1. Go to Settings > Hotspot & Tethering on your phone")
    print("2. Configure hotspot with 2.4GHz band (not 5GHz)")
    print("3. Note down the hotspot name and password")
    print("4. Turn ON the hotspot")
    print("\n⚠️  Important: Make sure your computer is connected to the SAME hotspot!")
    
    input("\nPress Enter when your hotspot is ON and your computer is connected to it...")
    
    # Get hotspot credentials
    print("\n📶 Enter your mobile hotspot details:")
    hotspot_ssid = input("Hotspot Name (SSID): ").strip()
    if not hotspot_ssid:
        print("❌ Hotspot name is required!")
        return
    
    hotspot_password = input("Hotspot Password: ").strip()
    if not hotspot_password:
        print("❌ Hotspot password is required!")
        return
    
    print(f"\n📋 Configuration Summary:")
    print(f"   Hotspot Name: {hotspot_ssid}")
    print(f"   Password: {'*' * len(hotspot_password)}")
    
    # Step 2: Try to configure via web interface first
    print(f"\n🌐 Step 1: Trying web interface configuration...")
    print("If ESP32-CAM is currently working, we'll try web config first")
    
    # Look for current ESP32-CAM
    config = MobileHotspotConfig()
    current_esp32_ips = config.scan_for_esp32_on_hotspot()
    
    web_config_success = False
    if current_esp32_ips:
        for ip in current_esp32_ips:
            print(f"🎯 Found ESP32-CAM at: {ip}")
            print(f"💡 Try opening: http://{ip}")
            print("Look for WiFi/Network settings to configure manually")
            
            try_web = input("Did you find WiFi settings in the web interface? (y/n): ").lower().strip()
            if try_web == 'y':
                input("Configure the WiFi settings in web interface, then press Enter...")
                web_config_success = True
                break
    
    # Step 3: Try serial configuration if web didn't work
    if not web_config_success:
        print(f"\n🔌 Step 2: Trying serial configuration...")
        print("Make sure ESP32-CAM is connected via USB")
        
        try_serial = input("Do you want to try serial configuration? (y/n): ").lower().strip()
        if try_serial == 'y':
            if config.connect_serial():
                config.configure_mobile_wifi(hotspot_ssid, hotspot_password)
                config.restart_device()
            else:
                print("❌ Serial configuration failed")
    
    # Step 4: Scan for ESP32-CAM on new network
    print(f"\n🔍 Step 3: Scanning for ESP32-CAM on mobile hotspot...")
    print("⏳ Waiting for ESP32-CAM to connect to your hotspot...")
    time.sleep(15)  # Give it time to connect
    
    esp32_ips = config.scan_for_esp32_on_hotspot()
    
    if esp32_ips:
        print(f"\n🎉 SUCCESS! ESP32-CAM found on mobile hotspot:")
        for ip in esp32_ips:
            print(f"   🎥 ESP32-CAM: http://{ip}")
        
        # Update config.py
        new_ip = esp32_ips[0]
        stream_url = f"http://{new_ip}/sustain?stream=0"
        
        print(f"\n📝 Updating config.py...")
        try:
            with open('config.py', 'r') as f:
                config_content = f.read()
            
            # Update the camera index
            import re
            pattern = r'CAMERA_INDEX = ["\'].*?["\']'
            new_line = f'CAMERA_INDEX = "{stream_url}"'
            config_content = re.sub(pattern, new_line, config_content)
            
            # Update ESP32-CAM IP settings
            pattern = r'ESP32_CAM_IP = ["\'].*?["\']'
            new_line = f'ESP32_CAM_IP = "{new_ip}"'
            config_content = re.sub(pattern, new_line, config_content)
            
            pattern = r'ESP32_CAM_WEB_INTERFACE = ["\'].*?["\']'
            new_line = f'ESP32_CAM_WEB_INTERFACE = "http://{new_ip}"'
            config_content = re.sub(pattern, new_line, config_content)
            
            pattern = r'ESP32_CAM_STREAM_URL = ["\'].*?["\']'
            new_line = f'ESP32_CAM_STREAM_URL = "{stream_url}"'
            config_content = re.sub(pattern, new_line, config_content)
            
            with open('config.py', 'w') as f:
                f.write(config_content)
            
            print("✅ config.py updated successfully!")
            
            # Save mobile config info
            with open("mobile_config.txt", "w") as f:
                f.write(f"ESP32-CAM Mobile Hotspot Configuration\n")
                f.write(f"=" * 50 + "\n")
                f.write(f"Hotspot Name: {hotspot_ssid}\n")
                f.write(f"ESP32-CAM IP: {new_ip}\n")
                f.write(f"Web Interface: http://{new_ip}\n")
                f.write(f"Stream URL: {stream_url}\n")
                f.write(f"Configuration Date: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            
            print(f"💾 Mobile configuration saved to: mobile_config.txt")
            
        except Exception as e:
            print(f"⚠️ Could not update config.py: {e}")
            print(f"💡 Manually update CAMERA_INDEX to: {stream_url}")
        
        print(f"\n🚀 Ready to use!")
        print(f"📱 Keep your mobile hotspot ON")
        print(f"🎥 Run: python motion_detector.py")
        
    else:
        print(f"\n❌ ESP32-CAM not found on mobile hotspot")
        print(f"\n🔧 Troubleshooting:")
        print(f"1. Make sure your phone's hotspot is using 2.4GHz (not 5GHz)")
        print(f"2. Check hotspot password is correct")
        print(f"3. Wait 2-3 minutes and run this script again")
        print(f"4. Try power cycling the ESP32-CAM")
        print(f"5. Check if ESP32-CAM creates its own WiFi network (means it didn't connect)")
    
    config.close()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Exiting...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure you have: pip install pyserial requests")