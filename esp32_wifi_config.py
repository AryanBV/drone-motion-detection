#!/usr/bin/env python3
"""
ESP32-CAM WiFi Configuration Tool
Configure ESP32-CAM to connect to your home WiFi network via serial
"""

import serial
import time
import sys

class ESP32WiFiConfig:
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
    
    def try_interactive_mode(self):
        """Try to enter interactive command mode"""
        print("\n🔧 Attempting to enter configuration mode...")
        
        # Try various ways to get attention
        commands = [
            "",  # Just enter
            "help",
            "config",
            "wifi",
            "menu",
            "setup",
            "settings",
            "AT",
            "AT+RST",
        ]
        
        for cmd in commands:
            response = self.send_command(cmd, 1)
            if response and any(keyword in response.lower() for keyword in 
                              ['menu', 'config', 'wifi', 'ssid', 'password', 'setup', '>', '$']):
                print(f"✅ Found interactive mode with command: '{cmd}'")
                return True
        
        print("⚠️ No interactive mode detected")
        return False
    
    def configure_wifi_manual(self, ssid, password):
        """Try manual WiFi configuration commands"""
        print(f"\n📶 Configuring WiFi: {ssid}")
        
        # Try different command formats
        wifi_commands = [
            f"wifi_config {ssid} {password}",
            f"setWiFi {ssid} {password}",
            f"AT+CWJAP=\"{ssid}\",\"{password}\"",
            f"wifi.config('{ssid}','{password}')",
            f"connect {ssid} {password}",
        ]
        
        for cmd in wifi_commands:
            print(f"\n🔧 Trying: {cmd}")
            response = self.send_command(cmd, 3)
            
            if response and any(keyword in response.lower() for keyword in 
                              ['ok', 'connected', 'success', 'wifi connected']):
                print("✅ WiFi configuration might have succeeded!")
                return True
        
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
        ]
        
        for cmd in restart_commands:
            response = self.send_command(cmd, 1)
            if response:
                break
        
        print("⏳ Waiting for restart...")
        time.sleep(5)
    
    def scan_for_device_on_network(self):
        """Scan for ESP32-CAM on the main network after configuration"""
        print("\n🔍 Scanning for ESP32-CAM on your WiFi network...")
        
        import socket
        import threading
        from concurrent.futures import ThreadPoolExecutor
        
        # Get local network
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        ip_base = ".".join(local_ip.split(".")[:-1]) + "."
        
        print(f"Scanning {ip_base}1-254 for ESP32-CAM...")
        
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
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = [executor.submit(check_ip, f"{ip_base}{i}") for i in range(1, 255)]
            
            for future in futures:
                result = future.result()
                if result and result != local_ip:
                    found_ips.append(result)
        
        if found_ips:
            print(f"✅ Found web servers at: {', '.join(found_ips)}")
            print("🎯 Try these URLs in your browser:")
            for ip in found_ips:
                print(f"   http://{ip}")
        else:
            print("❌ No ESP32-CAM found on network yet")
        
        return found_ips
    
    def close(self):
        """Close serial connection"""
        if self.ser:
            self.ser.close()

def main():
    print("ESP32-CAM WiFi Configuration Tool")
    print("=" * 50)
    
    # Get WiFi credentials
    print("📶 WiFi Configuration")
    ssid = input("Enter your WiFi name (SSID): ").strip()
    if not ssid:
        ssid = "Airtel_Salian"  # Default from screenshot
        print(f"Using default: {ssid}")
    
    password = input("Enter your WiFi password: ").strip()
    if not password:
        print("❌ Password required!")
        return
    
    # Connect to ESP32-CAM
    config = ESP32WiFiConfig()
    
    if not config.connect_serial():
        print("\n❌ Cannot connect to ESP32-CAM")
        print("🔧 Make sure:")
        print("1. ESP32-CAM is connected to USB")
        print("2. Device shows up as COM5 in Device Manager")
        print("3. No other programs are using the serial port")
        return
    
    try:
        # Try to enter interactive mode
        if config.try_interactive_mode():
            print("\n🎮 Interactive mode detected!")
            print("🔧 Try typing WiFi configuration commands manually:")
            print(f"   wifi_config {ssid} {password}")
            print(f"   setWiFi {ssid} {password}")
            print("   Type 'exit' to continue with automatic configuration")
            
            while True:
                user_cmd = input("ESP32> ").strip()
                if user_cmd.lower() == 'exit':
                    break
                elif user_cmd:
                    config.send_command(user_cmd)
        
        # Try automatic configuration
        print("\n🤖 Attempting automatic WiFi configuration...")
        config.configure_wifi_manual(ssid, password)
        
        # Restart device
        config.restart_device()
        
        # Wait a bit more for network connection
        print("⏳ Waiting for WiFi connection...")
        time.sleep(10)
        
        # Scan for device on network
        found_ips = config.scan_for_device_on_network()
        
        if found_ips:
            print(f"\n🎉 SUCCESS! ESP32-CAM might be at:")
            for ip in found_ips:
                print(f"   http://{ip}")
            print("\n🚀 Next steps:")
            print("1. Open the URL in your browser")
            print("2. Check if camera interface loads")
            print("3. Run the motion detection script with the stream URL")
        else:
            print(f"\n⚠️ ESP32-CAM not found on network yet")
            print("🔧 Troubleshooting:")
            print("1. Check WiFi password is correct")
            print("2. Wait longer for connection (try scanning again)")
            print("3. Check router's connected devices list")
            print("4. The device might still be in AP mode")
        
    finally:
        config.close()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Exiting...")
    except Exception as e:
        print(f"\n❌ Error: {e}")