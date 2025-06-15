#!/usr/bin/env python3
"""
Home Network ESP32-CAM Scanner
Find ESP32-CAM after it joins your home WiFi network
"""

import socket
import requests
import time
import threading
from concurrent.futures import ThreadPoolExecutor

def get_home_network_range():
    """Get your home network IP range"""
    try:
        # Connect to a remote server to get our local IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
        
        # Get network base (e.g., 192.168.1.x)
        ip_parts = local_ip.split('.')
        network_base = '.'.join(ip_parts[:3]) + '.'
        
        return local_ip, network_base
    except Exception as e:
        print(f"❌ Error getting network info: {e}")
        return None, None

def check_esp32_device(ip):
    """Check if IP is ESP32-CAM by testing web interface"""
    try:
        # Test web interface
        response = requests.get(f"http://{ip}", timeout=3)
        if response.status_code == 200:
            content = response.text.lower()
            
            # Check for ESP32-CAM indicators
            esp32_indicators = [
                'esp32', 'camera', 'stream', 'capture', 'mjpeg',
                'xiao', 'wifi setup', 'ota update'
            ]
            
            found_indicators = [ind for ind in esp32_indicators if ind in content]
            
            if found_indicators:
                return {
                    'ip': ip,
                    'likely_esp32': True,
                    'indicators': found_indicators,
                    'content_length': len(content)
                }
        
        # Also check common ESP32-CAM endpoints
        common_endpoints = ['/stream', '/capture', '/cam-hi.jpg']
        for endpoint in common_endpoints:
            try:
                resp = requests.get(f"http://{ip}{endpoint}", timeout=2)
                if resp.status_code == 200:
                    content_type = resp.headers.get('content-type', '').lower()
                    if 'image' in content_type or 'multipart' in content_type:
                        return {
                            'ip': ip,
                            'likely_esp32': True,
                            'indicators': [f'camera_endpoint_{endpoint}'],
                            'content_length': 0
                        }
            except:
                continue
                
    except:
        pass
    
    return None

def scan_for_esp32_on_home_network():
    """Scan home network for ESP32-CAM"""
    print("🏠 ESP32-CAM Home Network Scanner")
    print("=" * 50)
    
    # Get network info
    local_ip, network_base = get_home_network_range()
    if not network_base:
        print("❌ Cannot determine network range")
        return []
    
    print(f"📱 Your IP: {local_ip}")
    print(f"🔍 Scanning network: {network_base}*")
    print("⏳ This may take 30-60 seconds...")
    
    # First, scan for any web servers
    print("\n🔍 Step 1: Finding web servers...")
    web_servers = []
    
    def check_web_server(ip):
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
    
    # Scan network range
    with ThreadPoolExecutor(max_workers=50) as executor:
        futures = []
        for i in range(1, 255):
            ip = f"{network_base}{i}"
            if ip != local_ip:  # Skip our own IP
                future = executor.submit(check_web_server, ip)
                futures.append((ip, future))
        
        for ip, future in futures:
            result = future.result()
            if result:
                web_servers.append(ip)
                print(f"   📡 Found web server: {ip}")
    
    if not web_servers:
        print("❌ No web servers found on network")
        return []
    
    # Step 2: Check which web servers are ESP32-CAM
    print(f"\n🔍 Step 2: Testing {len(web_servers)} web servers for ESP32-CAM...")
    esp32_devices = []
    
    for ip in web_servers:
        print(f"Testing {ip}...", end=" ")
        result = check_esp32_device(ip)
        if result:
            esp32_devices.append(result)
            print(f"✅ ESP32-CAM found! Indicators: {result['indicators']}")
        else:
            print("❌ Not ESP32-CAM")
    
    return esp32_devices

def test_esp32_camera_functions(ip):
    """Test camera functions on found ESP32-CAM"""
    print(f"\n🎥 Testing camera functions on {ip}")
    print("-" * 40)
    
    base_url = f"http://{ip}"
    
    # Test common endpoints
    endpoints_to_test = [
        ('/', 'Web Interface'),
        ('/stream', 'Video Stream'),
        ('/capture', 'Image Capture'),
        ('/cam-hi.jpg', 'High-Res Image'),
        ('/cam-lo.jpg', 'Low-Res Image'),
        ('/status', 'Status Info')
    ]
    
    working_endpoints = []
    
    for endpoint, description in endpoints_to_test:
        url = f"{base_url}{endpoint}"
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                
                if 'image/jpeg' in content_type:
                    print(f"✅ {description}: {url} (Image)")
                    working_endpoints.append({'url': url, 'type': 'image', 'description': description})
                elif 'multipart' in content_type or 'mjpeg' in content_type:
                    print(f"✅ {description}: {url} (Stream)")
                    working_endpoints.append({'url': url, 'type': 'stream', 'description': description})
                elif 'text/html' in content_type:
                    print(f"✅ {description}: {url} (Web Page)")
                    working_endpoints.append({'url': url, 'type': 'html', 'description': description})
                else:
                    print(f"✅ {description}: {url} ({content_type})")
                    working_endpoints.append({'url': url, 'type': 'other', 'description': description})
            else:
                print(f"❌ {description}: HTTP {response.status_code}")
        except:
            print(f"❌ {description}: Connection failed")
    
    return working_endpoints

def main():
    print("🏠 ESP32-CAM Home Network Detection")
    print("=" * 60)
    print("Make sure you're connected to your home WiFi!")
    print("This will find ESP32-CAM devices on your home network.")
    
    input("\nPress Enter when you're connected to your home WiFi...")
    
    # Scan for ESP32-CAM devices
    esp32_devices = scan_for_esp32_on_home_network()
    
    if not esp32_devices:
        print("\n❌ No ESP32-CAM devices found on home network")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure ESP32-CAM WiFi configuration succeeded")
        print("2. Wait a few minutes for ESP32-CAM to connect")
        print("3. Check your router's connected devices list")
        print("4. ESP32-CAM might still be in AP mode")
        print("5. Try power cycling the ESP32-CAM")
        return
    
    # Display found devices
    print(f"\n🎉 Found {len(esp32_devices)} ESP32-CAM device(s)!")
    print("=" * 60)
    
    for i, device in enumerate(esp32_devices, 1):
        ip = device['ip']
        print(f"\n{i}. ESP32-CAM Device")
        print(f"   IP Address: {ip}")
        print(f"   Web Interface: http://{ip}")
        print(f"   Indicators: {device['indicators']}")
        
        # Test camera functions
        endpoints = test_esp32_camera_functions(ip)
        
        # Show usage instructions
        print(f"\n📋 Usage Instructions for {ip}:")
        
        # Find stream URL
        stream_urls = [ep['url'] for ep in endpoints if ep['type'] == 'stream']
        image_urls = [ep['url'] for ep in endpoints if ep['type'] == 'image']
        
        if stream_urls:
            print(f"🎥 For motion detection, use:")
            print(f"   cap = cv2.VideoCapture('{stream_urls[0]}')")
        elif image_urls:
            print(f"📸 For image-based detection, use:")
            print(f"   # Use requests.get('{image_urls[0]}') for images")
        
        print(f"🌐 Web interface: http://{ip}")
        
        # Save info to file
        with open("esp32_cam_info.txt", "w") as f:
            f.write(f"ESP32-CAM Configuration\n")
            f.write(f"=" * 30 + "\n")
            f.write(f"IP Address: {ip}\n")
            f.write(f"Web Interface: http://{ip}\n")
            f.write(f"Stream URL: {stream_urls[0] if stream_urls else 'Not found'}\n")
            f.write(f"Image URL: {image_urls[0] if image_urls else 'Not found'}\n")
            f.write(f"\nWorking Endpoints:\n")
            for ep in endpoints:
                f.write(f"  {ep['description']}: {ep['url']}\n")
        
        print(f"💾 Configuration saved to: esp32_cam_info.txt")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Exiting...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure you have requests installed: pip install requests")