#!/usr/bin/env python3
"""
Quick ESP32-CAM Finder
Rapidly scans your home network to find the ESP32-CAM
"""

import socket
import requests
import threading
import time
from concurrent.futures import ThreadPoolExecutor

def check_esp32_device(ip):
    """Check if IP is ESP32-CAM"""
    try:
        # Quick port check first
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((ip, 80))
        sock.close()
        
        if result != 0:
            return None
            
        # Test web interface
        response = requests.get(f"http://{ip}", timeout=5)
        if response.status_code == 200:
            content = response.text.lower()
            
            # Check for ESP32-CAM indicators
            esp32_indicators = [
                'esp32', 'camera', 'stream', 'capture', 'mjpeg',
                'wifi setup', 'ota update', 'xiao'
            ]
            
            found_indicators = [ind for ind in esp32_indicators if ind in content]
            
            if found_indicators:
                # Test camera endpoints
                endpoints = test_camera_endpoints(ip)
                return {
                    'ip': ip,
                    'indicators': found_indicators,
                    'endpoints': endpoints,
                    'content_preview': content[:200]
                }
        
        # Even if no indicators, test camera endpoints
        endpoints = test_camera_endpoints(ip)
        if endpoints:
            return {
                'ip': ip,
                'indicators': ['camera_endpoints_found'],
                'endpoints': endpoints,
                'content_preview': 'Camera endpoints detected'
            }
            
    except Exception as e:
        pass
    
    return None

def test_camera_endpoints(ip):
    """Test common camera endpoints"""
    endpoints = []
    test_paths = ['/stream', '/capture', '/cam-hi.jpg', '/cam-lo.jpg', '/video']
    
    for path in test_paths:
        try:
            resp = requests.get(f"http://{ip}{path}", timeout=3)
            if resp.status_code == 200:
                content_type = resp.headers.get('content-type', '').lower()
                if 'image' in content_type or 'multipart' in content_type:
                    endpoints.append({'path': path, 'type': content_type})
        except:
            continue
    
    return endpoints

def main():
    print("🔍 Quick ESP32-CAM Finder")
    print("=" * 50)
    
    # Get your network range
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    network_base = '.'.join(local_ip.split('.')[:-1]) + '.'
    
    print(f"📱 Your IP: {local_ip}")
    print(f"🔍 Scanning: {network_base}2-254")
    print("⏳ This will take about 30 seconds...")
    
    found_devices = []
    
    # Scan network range
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = []
        for i in range(2, 255):  # Skip .1 (router) and start from .2
            ip = f"{network_base}{i}"
            if ip != local_ip:
                future = executor.submit(check_esp32_device, ip)
                futures.append((ip, future))
        
        # Collect results
        for ip, future in futures:
            try:
                result = future.result()
                if result:
                    found_devices.append(result)
                    print(f"✅ Found ESP32-CAM at {ip}")
            except:
                continue
    
    # Display results
    print("\n" + "=" * 50)
    print("🎉 RESULTS")
    print("=" * 50)
    
    if found_devices:
        for device in found_devices:
            ip = device['ip']
            print(f"\n🎥 ESP32-CAM Found!")
            print(f"   IP Address: {ip}")
            print(f"   Web Interface: http://{ip}")
            print(f"   Indicators: {device['indicators']}")
            
            if device['endpoints']:
                print(f"   Camera Endpoints:")
                for ep in device['endpoints']:
                    print(f"     http://{ip}{ep['path']} ({ep['type']})")
            
            print(f"\n🚀 NEXT STEPS:")
            print(f"1. Open browser: http://{ip}")
            print(f"2. Update config.py:")
            
            # Suggest the best stream URL
            stream_endpoints = [ep for ep in device['endpoints'] if 'stream' in ep['path']]
            if stream_endpoints:
                print(f"   CAMERA_INDEX = \"http://{ip}{stream_endpoints[0]['path']}\"")
            else:
                print(f"   CAMERA_INDEX = \"http://{ip}/stream\"  # Try this")
            
            # Save to file
            with open("esp32_found.txt", "w") as f:
                f.write(f"ESP32-CAM Found!\n")
                f.write(f"IP: {ip}\n")
                f.write(f"Web Interface: http://{ip}\n")
                if stream_endpoints:
                    f.write(f"Stream URL: http://{ip}{stream_endpoints[0]['path']}\n")
                else:
                    f.write(f"Stream URL: http://{ip}/stream\n")
            
            print(f"💾 Info saved to: esp32_found.txt")
    
    else:
        print("❌ No ESP32-CAM devices found")
        print("\n🔧 Try these steps:")
        print("1. Check router admin panel (Method 1 above)")
        print("2. Wait 2-3 minutes and run this script again")
        print("3. Power cycle the ESP32-CAM")
        print("4. Check if ESP32-CAM WiFi network reappeared")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n👋 Scanning interrupted")
    except Exception as e:
        print(f"❌ Error: {e}")
        print("Make sure you have: pip install requests")