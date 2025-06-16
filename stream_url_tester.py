#!/usr/bin/env python3
"""
ESP32-CAM Stream URL Tester
Test all possible stream endpoints to find working ones
"""

import cv2
import requests
import time
import socket
from concurrent.futures import ThreadPoolExecutor

def test_basic_connection(ip, port=80):
    """Test basic TCP connection"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((ip, port))
        sock.close()
        return result == 0
    except:
        return False

def test_http_endpoints(ip):
    """Test all possible HTTP endpoints"""
    endpoints = [
        "/",
        "/stream",
        "/video", 
        "/mjpeg",
        "/sustain?stream=0",
        "/cam-hi.jpg",
        "/cam-lo.jpg",
        "/cam-mid.jpg",
        "/capture",
        "/snapshot",
        "/jpg",
        "/live",
        "/camera",
        "/webcam",
        "/feed",
        "/view",
        ":81/stream",
        ":8080/stream",
        ":8081/stream",
    ]
    
    working_endpoints = []
    
    print(f"🔍 Testing HTTP endpoints on {ip}...")
    
    for endpoint in endpoints:
        if endpoint.startswith(':'):
            # Different port
            port = endpoint.split('/')[0][1:]
            path = '/' + '/'.join(endpoint.split('/')[1:])
            url = f"http://{ip}:{port}{path}"
        else:
            url = f"http://{ip}{endpoint}"
        
        try:
            print(f"   Testing: {url}")
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                content_length = len(response.content)
                
                result = {
                    'url': url,
                    'status': response.status_code,
                    'content_type': content_type,
                    'size': content_length
                }
                
                if 'image/jpeg' in content_type:
                    result['type'] = 'JPEG Image'
                    print(f"   ✅ JPEG Image: {url} ({content_length} bytes)")
                elif 'multipart' in content_type or 'mjpeg' in content_type:
                    result['type'] = 'MJPEG Stream'
                    print(f"   ✅ MJPEG Stream: {url}")
                elif 'text/html' in content_type:
                    result['type'] = 'HTML Page'
                    print(f"   ✅ HTML Page: {url} ({content_length} bytes)")
                else:
                    result['type'] = 'Other'
                    print(f"   ✅ Response: {url} - {content_type}")
                
                working_endpoints.append(result)
            else:
                print(f"   ❌ HTTP {response.status_code}: {url}")
                
        except requests.exceptions.Timeout:
            print(f"   ⏰ Timeout: {url}")
        except requests.exceptions.ConnectionError:
            print(f"   ❌ Connection failed: {url}")
        except Exception as e:
            print(f"   ❌ Error: {url} - {e}")
    
    return working_endpoints

def test_opencv_compatibility(urls):
    """Test which URLs work with OpenCV"""
    print(f"\n🎥 Testing OpenCV compatibility...")
    opencv_working = []
    
    for url_info in urls:
        url = url_info['url']
        url_type = url_info.get('type', 'Unknown')
        
        if url_type in ['MJPEG Stream', 'Other']:
            print(f"\n🔍 Testing OpenCV with: {url}")
            
            try:
                cap = cv2.VideoCapture(url)
                
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        height, width = frame.shape[:2]
                        print(f"   ✅ OpenCV SUCCESS: {url}")
                        print(f"   📐 Resolution: {width}x{height}")
                        
                        opencv_working.append({
                            'url': url,
                            'width': width,
                            'height': height,
                            'type': url_type
                        })
                    else:
                        print(f"   ❌ OpenCV can't read frames: {url}")
                else:
                    print(f"   ❌ OpenCV can't open: {url}")
                
                cap.release()
                
            except Exception as e:
                print(f"   ❌ OpenCV error: {url} - {e}")
    
    return opencv_working

def test_image_polling(urls):
    """Test image polling for JPEG endpoints"""
    print(f"\n📸 Testing image polling (for JPEG endpoints)...")
    
    jpeg_urls = [u for u in urls if u.get('type') == 'JPEG Image']
    
    if not jpeg_urls:
        print(f"   ❌ No JPEG endpoints found for polling")
        return []
    
    working_polling = []
    
    for url_info in jpeg_urls:
        url = url_info['url']
        print(f"\n🔍 Testing image polling: {url}")
        
        try:
            # Test multiple rapid requests
            for i in range(3):
                response = requests.get(url, timeout=3)
                if response.status_code == 200 and len(response.content) > 1000:
                    print(f"   ✅ Poll {i+1}: {len(response.content)} bytes")
                else:
                    print(f"   ❌ Poll {i+1}: Failed")
                    break
                time.sleep(0.5)
            else:
                # All polls succeeded
                working_polling.append(url_info)
                print(f"   ✅ Image polling works: {url}")
                
        except Exception as e:
            print(f"   ❌ Polling failed: {url} - {e}")
    
    return working_polling

def create_motion_config(opencv_urls, polling_urls):
    """Create motion detection config suggestions"""
    print(f"\n📝 Motion Detection Configuration:")
    print(f"="*50)
    
    if opencv_urls:
        best_stream = opencv_urls[0]
        print(f"🎯 RECOMMENDED: Use OpenCV streaming")
        print(f"   URL: {best_stream['url']}")
        print(f"   Resolution: {best_stream['width']}x{best_stream['height']}")
        print(f"")
        print(f"📋 Update your config.py:")
        print(f"   CAMERA_INDEX = \"{best_stream['url']}\"")
        print(f"")
        print(f"🚀 Run motion detection:")
        print(f"   python motion_detector.py")
        
        return best_stream['url']
        
    elif polling_urls:
        best_polling = polling_urls[0]
        print(f"🎯 ALTERNATIVE: Use image polling (slower)")
        print(f"   URL: {best_polling['url']}")
        print(f"")
        print(f"⚠️  Note: Image polling requires different motion detection code")
        print(f"   This polls for individual images instead of video stream")
        
        return best_polling['url']
        
    else:
        print(f"❌ No suitable URLs found for motion detection")
        print(f"")
        print(f"🔧 Possible solutions:")
        print(f"1. Flash different firmware with proper streaming support")
        print(f"2. Use a different ESP32-CAM module") 
        print(f"3. Check if device needs specific configuration")
        
        return None

def main():
    esp32_ip = "192.168.195.193"
    
    print(f"🔍 ESP32-CAM Stream URL Tester")
    print(f"="*50)
    print(f"Target: {esp32_ip}")
    print(f"")
    
    # Step 1: Test basic connection
    print(f"📡 Step 1: Testing basic connection...")
    if test_basic_connection(esp32_ip):
        print(f"   ✅ TCP connection successful on port 80")
    else:
        print(f"   ❌ No TCP connection on port 80")
        print(f"   🔧 Try:")
        print(f"   1. Power cycle ESP32-CAM")
        print(f"   2. Move closer to phone")
        print(f"   3. Check WiFi stability")
        return
    
    # Step 2: Test HTTP endpoints  
    print(f"\n📡 Step 2: Testing HTTP endpoints...")
    working_urls = test_http_endpoints(esp32_ip)
    
    if not working_urls:
        print(f"\n❌ No HTTP endpoints found!")
        print(f"🔧 This suggests:")
        print(f"   1. Firmware doesn't have web server")
        print(f"   2. Web server not started")
        print(f"   3. Different port being used")
        return
    
    print(f"\n✅ Found {len(working_urls)} working endpoints:")
    for url in working_urls:
        print(f"   {url['type']}: {url['url']}")
    
    # Step 3: Test OpenCV compatibility
    opencv_urls = test_opencv_compatibility(working_urls)
    
    # Step 4: Test image polling
    polling_urls = test_image_polling(working_urls)
    
    # Step 5: Create configuration
    recommended_url = create_motion_config(opencv_urls, polling_urls)
    
    if recommended_url:
        # Save configuration
        with open("working_stream_config.txt", "w") as f:
            f.write(f"ESP32-CAM Working Stream Configuration\n")
            f.write(f"="*50 + "\n")
            f.write(f"IP Address: {esp32_ip}\n")
            f.write(f"Recommended URL: {recommended_url}\n")
            f.write(f"\nAll Working URLs:\n")
            for url in working_urls:
                f.write(f"  {url['type']}: {url['url']}\n")
            f.write(f"\nOpenCV Compatible:\n")
            for url in opencv_urls:
                f.write(f"  {url['url']} - {url['width']}x{url['height']}\n")
        
        print(f"\n💾 Configuration saved to: working_stream_config.txt")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n👋 Testing interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")