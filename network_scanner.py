#!/usr/bin/env python3
"""
ESP32-CAM Network Scanner
Finds ESP32-CAM devices on the network and tests web interface
"""

import socket
import requests
import time
import threading
from concurrent.futures import ThreadPoolExecutor

def scan_port(ip, port, timeout=1):
    """Check if a port is open on an IP address"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except:
        return False

def test_esp32_cam_web(ip):
    """Test if an IP has ESP32-CAM web interface"""
    try:
        # Common ESP32-CAM web interface paths
        test_urls = [
            f"http://{ip}",
            f"http://{ip}/",
            f"http://{ip}/cam-hi.jpg",
            f"http://{ip}/capture",
            f"http://{ip}/stream",
        ]
        
        for url in test_urls:
            try:
                response = requests.get(url, timeout=3)
                if response.status_code == 200:
                    content = response.text.lower()
                    if any(keyword in content for keyword in ['esp32', 'camera', 'stream', 'mjpeg']):
                        return True, url, "ESP32-CAM Web Interface Found!"
                    else:
                        return True, url, "Web server found (might be ESP32-CAM)"
            except:
                continue
        
        return False, None, None
        
    except Exception as e:
        return False, None, str(e)

def scan_network():
    """Scan local network for ESP32-CAM devices"""
    print("🔍 Scanning for ESP32-CAM devices...")
    print("=" * 60)
    
    # Get local network range
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    print(f"Your computer IP: {local_ip}")
    
    # Common ESP32-CAM IP ranges
    ip_ranges = [
        "192.168.4.",    # ESP32 AP mode default
        "192.168.1.",    # Common home router range
        "192.168.0.",    # Another common range
        ".".join(local_ip.split(".")[:-1]) + "."  # Same subnet as computer
    ]
    
    found_devices = []
    
    for ip_base in ip_ranges:
        if ip_base == ".".join(local_ip.split(".")[:-1]) + "." and ip_base in [r for r in ip_ranges[:-1]]:
            continue  # Skip duplicate ranges
            
        print(f"\nScanning {ip_base}1-254...")
        
        # Use threading to speed up scanning
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = []
            
            for i in range(1, 255):
                ip = f"{ip_base}{i}"
                if ip == local_ip:
                    continue
                    
                # Submit port 80 scan
                future = executor.submit(scan_port, ip, 80, 0.5)
                futures.append((ip, future))
            
            # Check results
            for ip, future in futures:
                try:
                    if future.result():
                        print(f"Found web server at {ip}:80")
                        
                        # Test if it's ESP32-CAM
                        is_esp32, url, description = test_esp32_cam_web(ip)
                        if is_esp32:
                            found_devices.append({
                                'ip': ip,
                                'url': url,
                                'description': description
                            })
                            print(f"✅ {ip} - {description}")
                        else:
                            print(f"ℹ️  {ip} - Web server (not ESP32-CAM)")
                            
                except:
                    continue
    
    return found_devices

def test_common_esp32_ips():
    """Test common ESP32-CAM IP addresses"""
    print("\n🎯 Testing common ESP32-CAM IP addresses...")
    print("=" * 60)
    
    common_ips = [
        "192.168.4.1",   # Default ESP32 AP mode
        "192.168.1.100", # Common static IP
        "192.168.1.200",
        "192.168.0.100",
        "192.168.0.200",
    ]
    
    found_devices = []
    
    for ip in common_ips:
        print(f"Testing {ip}...", end=" ")
        
        if scan_port(ip, 80, 2):
            is_esp32, url, description = test_esp32_cam_web(ip)
            if is_esp32:
                found_devices.append({
                    'ip': ip,
                    'url': url,
                    'description': description
                })
                print(f"✅ {description}")
            else:
                print("ℹ️  Web server found (not ESP32-CAM)")
        else:
            print("❌ No response")
    
    return found_devices

def main():
    print("ESP32-CAM Network Discovery Tool")
    print("=" * 60)
    
    # First test common IPs (faster)
    common_devices = test_common_esp32_ips()
    
    # Then do full network scan if needed
    if not common_devices:
        all_devices = scan_network()
    else:
        all_devices = common_devices
    
    print("\n" + "=" * 60)
    print("🎉 RESULTS")
    print("=" * 60)
    
    if all_devices:
        print(f"Found {len(all_devices)} ESP32-CAM device(s):")
        
        for i, device in enumerate(all_devices, 1):
            print(f"\n{i}. ESP32-CAM Device:")
            print(f"   IP Address: {device['ip']}")
            print(f"   Web Interface: {device['url']}")
            print(f"   Description: {device['description']}")
            print(f"   📱 Open in browser: http://{device['ip']}")
        
        print(f"\n🚀 NEXT STEPS:")
        print(f"1. Open your web browser")
        print(f"2. Go to: http://{all_devices[0]['ip']}")
        print(f"3. You should see the ESP32-CAM web interface!")
        print(f"4. Look for camera controls and live stream")
        
    else:
        print("❌ No ESP32-CAM devices found on the network")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure the ESP32-CAM is powered and connected")
        print("2. Check if it creates its own WiFi network (ESP32-CAM_XXXX)")
        print("3. Try connecting to its WiFi network first")
        print("4. The device might need 30-60 seconds to boot up completely")

if __name__ == "__main__":
    main()