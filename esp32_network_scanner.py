#!/usr/bin/env python3
"""
ESP32-CAM Network Scanner (for when connected to ESP32 WiFi)
Finds the correct IP and port for ESP32-CAM web interface
"""

import socket
import requests
import time
import threading
from concurrent.futures import ThreadPoolExecutor

def get_current_network_info():
    """Get current network information"""
    try:
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"📱 Your device IP: {local_ip}")
        
        # Determine network range
        ip_parts = local_ip.split('.')
        network_base = '.'.join(ip_parts[:3]) + '.'
        
        return local_ip, network_base
    except Exception as e:
        print(f"❌ Network info error: {e}")
        return None, None

def scan_ip_port(ip, port, timeout=1):
    """Check if specific IP:port is accessible"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except:
        return False

def test_web_interface(ip, port=80):
    """Test if IP has a web interface and what it serves"""
    try:
        base_url = f"http://{ip}" if port == 80 else f"http://{ip}:{port}"
        
        # Test basic connection
        response = requests.get(base_url, timeout=5)
        if response.status_code == 200:
            content = response.text.lower()
            
            # Check for camera-related content
            camera_keywords = ['camera', 'stream', 'video', 'mjpeg', 'snapshot', 'capture', 'esp32']
            
            found_keywords = [kw for kw in camera_keywords if kw in content]
            
            return {
                'accessible': True,
                'url': base_url,
                'content_length': len(content),
                'keywords': found_keywords,
                'title': extract_title(content),
                'likely_camera': len(found_keywords) > 0
            }
        else:
            return {
                'accessible': True,
                'url': base_url,
                'status_code': response.status_code,
                'likely_camera': False
            }
    except Exception as e:
        return {'accessible': False, 'error': str(e)}

def extract_title(html_content):
    """Extract title from HTML content"""
    try:
        import re
        title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_content, re.IGNORECASE)
        if title_match:
            return title_match.group(1).strip()
    except:
        pass
    return "No title"

def scan_common_camera_endpoints(base_ip):
    """Test common camera endpoints on found IPs"""
    
    common_endpoints = [
        "/",
        "/cam-hi.jpg",
        "/cam-lo.jpg", 
        "/cam-mid.jpg",
        "/capture",
        "/snapshot.jpg",
        "/stream",
        "/video",
        "/mjpeg",
        "/live",
        "/index.html",
        "/camera.html",
        "/cam.html"
    ]
    
    results = []
    
    for endpoint in common_endpoints:
        url = f"http://{base_ip}{endpoint}"
        try:
            response = requests.get(url, timeout=3)
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                
                result = {
                    'url': url,
                    'status': response.status_code,
                    'content_type': content_type,
                    'size': len(response.content)
                }
                
                if 'image/jpeg' in content_type:
                    result['type'] = 'Image'
                elif 'multipart' in content_type or 'mjpeg' in content_type:
                    result['type'] = 'Video Stream'
                elif 'text/html' in content_type:
                    result['type'] = 'Web Page'
                else:
                    result['type'] = 'Unknown'
                
                results.append(result)
                print(f"✅ {url} - {result['type']} ({result['content_type']})")
                
        except Exception as e:
            continue
    
    return results

def comprehensive_scan():
    """Comprehensive scan of ESP32-CAM network"""
    print("ESP32-CAM Network Scanner (Connected Mode)")
    print("=" * 60)
    
    # Get network info
    local_ip, network_base = get_current_network_info()
    if not network_base:
        print("❌ Cannot determine network range")
        return
    
    print(f"🔍 Scanning network: {network_base}*")
    print(f"📱 Your IP: {local_ip}")
    
    # Common ESP32-CAM IP addresses to try first
    priority_ips = [
        "192.168.4.1",
        "192.168.4.2", 
        "192.168.1.1",
        "10.0.0.1",
        f"{network_base}1"
    ]
    
    # Add network range IPs
    network_ips = [f"{network_base}{i}" for i in range(1, 255) if f"{network_base}{i}" != local_ip]
    
    # Combine and remove duplicates
    all_ips = list(dict.fromkeys(priority_ips + network_ips))
    
    print(f"\n🎯 Testing priority IPs first...")
    
    # Test priority IPs on multiple ports
    ports_to_test = [80, 8080, 8000, 8081, 3000, 5000]
    
    found_services = []
    
    # Test priority IPs first
    for ip in priority_ips:
        for port in ports_to_test:
            if scan_ip_port(ip, port, 2):
                print(f"🔍 Found service at {ip}:{port}")
                web_result = test_web_interface(ip, port)
                if web_result.get('accessible'):
                    found_services.append({
                        'ip': ip,
                        'port': port,
                        'info': web_result
                    })
                    print(f"   📊 {web_result}")
    
    # If nothing found, scan full network on port 80
    if not found_services:
        print(f"\n🔍 Scanning full network range on port 80...")
        
        with ThreadPoolExecutor(max_workers=50) as executor:
            futures = []
            for ip in network_ips[:50]:  # Limit to first 50 IPs for speed
                future = executor.submit(scan_ip_port, ip, 80, 1)
                futures.append((ip, future))
            
            for ip, future in futures:
                if future.result():
                    web_result = test_web_interface(ip, 80)
                    if web_result.get('accessible'):
                        found_services.append({
                            'ip': ip,
                            'port': 80,
                            'info': web_result
                        })
                        print(f"✅ Found web service at {ip}")
    
    # Display results
    print(f"\n{'=' * 60}")
    print(f"🎉 RESULTS")
    print(f"{'=' * 60}")
    
    if found_services:
        print(f"Found {len(found_services)} web service(s):")
        
        for i, service in enumerate(found_services, 1):
            ip = service['ip']
            port = service['port']
            info = service['info']
            
            print(f"\n{i}. Web Service at {ip}:{port}")
            print(f"   URL: {info.get('url', f'http://{ip}:{port}')}")
            print(f"   Title: {info.get('title', 'Unknown')}")
            print(f"   Keywords: {info.get('keywords', [])}")
            
            if info.get('likely_camera'):
                print(f"   🎥 LIKELY CAMERA INTERFACE!")
                
                # Test camera endpoints
                print(f"   🔍 Testing camera endpoints...")
                endpoints = scan_common_camera_endpoints(ip if port == 80 else f"{ip}:{port}")
                
                if endpoints:
                    print(f"   📹 Camera endpoints found:")
                    for ep in endpoints:
                        print(f"      {ep['url']} - {ep['type']}")
                else:
                    print(f"   ⚠️ No camera endpoints found")
            
            print(f"   📱 Open in browser: {info.get('url')}")
    
    else:
        print("❌ No web services found")
        print("\n🔧 Troubleshooting:")
        print("1. ESP32-CAM might not have web interface enabled")
        print("2. Check if device is in programming mode vs run mode") 
        print("3. Try pressing RESET button on ESP32-CAM")
        print("4. Web server might be starting - wait 30 seconds and try again")
        print("5. Check for any buttons on the device to enable camera mode")

def quick_test():
    """Quick test of most common ESP32-CAM addresses"""
    print("🚀 Quick ESP32-CAM Test")
    print("=" * 30)
    
    test_urls = [
        "http://192.168.4.1",
        "http://192.168.4.1:80", 
        "http://192.168.4.1:8080",
        "http://192.168.4.2",
        "http://192.168.1.1",
        "http://10.0.0.1"
    ]
    
    for url in test_urls:
        print(f"Testing {url}...", end=" ")
        try:
            response = requests.get(url, timeout=3)
            print(f"✅ {response.status_code} - Content: {len(response.text)} chars")
            
            # If successful, test camera endpoints
            if response.status_code == 200:
                base_url = url.split('//')[1].split(':')[0] if ':' in url.split('//')[1] else url.split('//')[1]
                endpoints = scan_common_camera_endpoints(base_url)
                if endpoints:
                    print(f"   🎥 Camera endpoints:")
                    for ep in endpoints[:3]:  # Show first 3
                        print(f"      {ep['url']}")
        except:
            print("❌ Failed")

if __name__ == "__main__":
    print("Choose scan type:")
    print("1. Quick test (recommended)")
    print("2. Comprehensive scan")
    
    try:
        choice = input("Enter choice (1 or 2): ").strip()
        if choice == "2":
            comprehensive_scan()
        else:
            quick_test()
    except KeyboardInterrupt:
        print("\n\n👋 Exiting...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("Make sure you have: pip install requests")