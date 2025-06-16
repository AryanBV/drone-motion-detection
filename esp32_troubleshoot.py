#!/usr/bin/env python3
"""
ESP32-CAM Troubleshooting Tool
Find ESP32-CAM on mobile hotspot and test all possible endpoints
"""

import socket
import requests
import time
import threading
from concurrent.futures import ThreadPoolExecutor

def ping_ip(ip):
    """Test if IP responds to basic connection"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((ip, 80))
        sock.close()
        return result == 0
    except:
        return False

def test_esp32_endpoints(ip):
    """Test all possible ESP32-CAM endpoints"""
    endpoints = [
        "/",
        "/stream",
        "/sustain?stream=0", 
        "/capture",
        "/cam-hi.jpg",
        "/cam-lo.jpg",
        "/status",
        "/config",
        "/wifi",
    ]
    
    ports = [80, 8080, 8081, 3000, 5000]
    
    working_endpoints = []
    
    print(f"🔍 Testing {ip} on multiple ports and endpoints...")
    
    for port in ports:
        print(f"   Testing port {port}...")
        
        # Test basic connection first
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((ip, port))
            sock.close()
            
            if result == 0:
                print(f"   ✅ Port {port} is open!")
                
                # Test endpoints on this port
                for endpoint in endpoints:
                    try:
                        if port == 80:
                            url = f"http://{ip}{endpoint}"
                        else:
                            url = f"http://{ip}:{port}{endpoint}"
                        
                        response = requests.get(url, timeout=3)
                        if response.status_code == 200:
                            content_type = response.headers.get('content-type', '')
                            working_endpoints.append({
                                'url': url,
                                'status': response.status_code,
                                'content_type': content_type,
                                'size': len(response.content)
                            })
                            print(f"   ✅ Working: {url}")
                        
                    except Exception as e:
                        continue
            else:
                print(f"   ❌ Port {port} closed")
                
        except Exception as e:
            print(f"   ❌ Port {port} error: {e}")
    
    return working_endpoints

def scan_mobile_network():
    """Scan entire mobile network for ESP32-CAM"""
    print("🔍 Scanning mobile hotspot network for ESP32-CAM...")
    
    # Get current network
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        
        network_base = '.'.join(local_ip.split('.')[:-1]) + '.'
        print(f"📱 Your IP: {local_ip}")
        print(f"🔍 Scanning: {network_base}1-254")
        
    except Exception as e:
        print(f"❌ Cannot determine network: {e}")
        return []
    
    # Quick ping scan first
    print("📡 Quick ping scan...")
    responsive_ips = []
    
    def ping_test(ip):
        if ping_ip(ip):
            return ip
        return None
    
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = []
        for i in range(1, 255):
            ip = f"{network_base}{i}"
            if ip != local_ip:
                future = executor.submit(ping_test, ip)
                futures.append(future)
        
        for future in futures:
            result = future.result()
            if result:
                responsive_ips.append(result)
                print(f"✅ Responsive: {result}")
    
    return responsive_ips

def check_esp32_status_via_serial():
    """Check ESP32-CAM status via serial"""
    print("\n🔌 Checking ESP32-CAM via serial...")
    
    try:
        import serial
        
        ser = serial.Serial("COM5", 115200, timeout=2)
        time.sleep(2)
        
        # Send status commands
        commands = [
            "",  # Just enter
            "status",
            "ip",
            "wifi",
            "AT+CIFSR",  # Get IP
        ]
        
        for cmd in commands:
            ser.flushInput()
            ser.flushOutput()
            ser.write((cmd + '\r\n').encode())
            time.sleep(1)
            
            response = ""
            while ser.in_waiting > 0:
                response += ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                time.sleep(0.1)
            
            if response.strip():
                print(f"📤 {cmd}: {response.strip()}")
                
                # Look for IP addresses in response
                import re
                ip_matches = re.findall(r'192\.168\.195\.(\d+)', response)
                if ip_matches:
                    for match in ip_matches:
                        potential_ip = f"192.168.195.{match}"
                        print(f"🎯 Found potential IP: {potential_ip}")
        
        ser.close()
        return True
        
    except Exception as e:
        print(f"❌ Serial check failed: {e}")
        return False

def main():
    print("🔧 ESP32-CAM Troubleshooting Tool")
    print("=" * 50)
    
    # Step 1: Test the known IP
    known_ip = "192.168.195.193"
    print(f"\n📍 Step 1: Testing known IP {known_ip}")
    
    if ping_ip(known_ip):
        print(f"✅ {known_ip} responds to ping!")
        endpoints = test_esp32_endpoints(known_ip)
        
        if endpoints:
            print(f"\n🎉 ESP32-CAM found at {known_ip}!")
            for ep in endpoints:
                print(f"   {ep['url']} - {ep['content_type']}")
            return
        else:
            print(f"⚠️ {known_ip} responds but no web server found")
    else:
        print(f"❌ {known_ip} not responding")
    
    # Step 2: Check serial for current status
    print(f"\n🔌 Step 2: Checking serial connection")
    check_esp32_status_via_serial()
    
    # Step 3: Scan entire network
    print(f"\n🔍 Step 3: Scanning entire mobile network")
    responsive_ips = scan_mobile_network()
    
    if responsive_ips:
        print(f"\n📡 Found {len(responsive_ips)} responsive IPs")
        
        for ip in responsive_ips:
            print(f"\n🔍 Testing {ip} for ESP32-CAM...")
            endpoints = test_esp32_endpoints(ip)
            
            if endpoints:
                print(f"🎥 ESP32-CAM found at {ip}!")
                for ep in endpoints:
                    print(f"   {ep['url']}")
                
                # Update config suggestion
                print(f"\n📝 Update your config.py:")
                print(f"   CAMERA_INDEX = \"http://{ip}/sustain?stream=0\"")
                return
    
    # Step 4: Recommendations
    print(f"\n🔧 Recommendations:")
    print(f"1. Power cycle ESP32-CAM (unplug and replug)")
    print(f"2. Wait 30 seconds for boot up")
    print(f"3. Check serial monitor for new IP")
    print(f"4. Try rerunning this script")
    print(f"5. Check if ESP32-CAM creates its own WiFi network")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Interrupted")
    except Exception as e:
        print(f"❌ Error: {e}")