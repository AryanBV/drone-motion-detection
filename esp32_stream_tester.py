#!/usr/bin/env python3
"""
ESP32-CAM Stream URL Finder and Tester
Tests different stream endpoints to find the working camera stream
"""

import requests
import cv2
import time

def test_esp32_stream_urls(ip):
    """Test different possible stream URLs for ESP32-CAM"""
    
    print(f"🔍 Testing ESP32-CAM stream URLs for {ip}")
    print("=" * 60)
    
    # Common ESP32-CAM stream endpoints
    stream_urls = [
        f"http://{ip}/stream",
        f"http://{ip}/mjpeg",
        f"http://{ip}/video",
        f"http://{ip}/cam",
        f"http://{ip}/live",
        f"http://{ip}:81/stream",
        f"http://{ip}/capture",
        f"http://{ip}/cam-hi.jpg",
        f"http://{ip}/cam-lo.jpg",
        f"http://{ip}/jpg",
        f"http://{ip}/camera",
    ]
    
    working_urls = []
    
    for url in stream_urls:
        print(f"Testing: {url}")
        
        try:
            # Test with requests first
            response = requests.get(url, timeout=5, stream=True)
            
            if response.status_code == 200:
                content_type = response.headers.get('content-type', '').lower()
                
                if 'multipart' in content_type or 'mjpeg' in content_type:
                    print(f"✅ MJPEG Stream: {url}")
                    working_urls.append({'url': url, 'type': 'mjpeg_stream'})
                    
                elif 'image/jpeg' in content_type:
                    print(f"✅ JPEG Image: {url}")
                    working_urls.append({'url': url, 'type': 'jpeg_image'})
                    
                elif 'video' in content_type:
                    print(f"✅ Video Stream: {url}")
                    working_urls.append({'url': url, 'type': 'video_stream'})
                    
                else:
                    print(f"⚠️ Unknown content: {url} ({content_type})")
                    working_urls.append({'url': url, 'type': 'unknown'})
            else:
                print(f"❌ HTTP {response.status_code}: {url}")
                
        except Exception as e:
            print(f"❌ Failed: {url} - {e}")
    
    return working_urls

def test_opencv_stream(url):
    """Test if OpenCV can read the stream"""
    print(f"\n🎥 Testing OpenCV compatibility: {url}")
    
    try:
        cap = cv2.VideoCapture(url)
        
        if not cap.isOpened():
            print(f"❌ OpenCV cannot open: {url}")
            return False
        
        # Try to read a frame
        ret, frame = cap.read()
        if not ret:
            print(f"❌ OpenCV cannot read frames: {url}")
            cap.release()
            return False
        
        print(f"✅ OpenCV SUCCESS: {url}")
        print(f"   Resolution: {frame.shape[1]}x{frame.shape[0]}")
        print(f"   Channels: {frame.shape[2] if len(frame.shape) > 2 else 1}")
        
        # Test a few more frames
        for i in range(3):
            ret, frame = cap.read()
            if ret:
                print(f"   Frame {i+2}: OK")
            else:
                print(f"   Frame {i+2}: Failed")
                break
        
        cap.release()
        return True
        
    except Exception as e:
        print(f"❌ OpenCV error: {e}")
        return False

def main():
    # Your ESP32-CAM IP
    esp32_ip = "192.168.1.5"
    
    print("ESP32-CAM Stream URL Finder")
    print("=" * 60)
    print(f"Target device: {esp32_ip}")
    print("Make sure you've clicked 'Start Stream' in the web interface first!")
    
    input("Press Enter when stream is started...")
    
    # Test different URLs
    working_urls = test_esp32_stream_urls(esp32_ip)
    
    if not working_urls:
        print("\n❌ No working stream URLs found!")
        print("\n🔧 Try these steps:")
        print("1. Make sure you clicked 'Start Stream' in web interface")
        print("2. Check if stream opens in a new browser tab")
        print("3. Note the URL of that new tab")
        print("4. Try different ports (81, 8080, 8081)")
        return
    
    print(f"\n🎉 Found {len(working_urls)} working URL(s):")
    print("=" * 60)
    
    # Test with OpenCV
    opencv_compatible = []
    
    for i, url_info in enumerate(working_urls, 1):
        url = url_info['url']
        url_type = url_info['type']
        
        print(f"\n{i}. {url} ({url_type})")
        
        if url_type in ['mjpeg_stream', 'video_stream']:
            if test_opencv_stream(url):
                opencv_compatible.append(url)
    
    # Show final recommendations
    print("\n" + "=" * 60)
    print("🚀 FINAL RECOMMENDATIONS")
    print("=" * 60)
    
    if opencv_compatible:
        best_url = opencv_compatible[0]
        print(f"✅ Best stream URL for motion detection:")
        print(f"   {best_url}")
        print(f"\n📝 Update your config.py:")
        print(f"   CAMERA_INDEX = \"{best_url}\"")
        
        # Save to file
        with open("esp32_stream_config.txt", "w") as f:
            f.write(f"ESP32-CAM Stream Configuration\n")
            f.write(f"=" * 40 + "\n")
            f.write(f"IP Address: {esp32_ip}\n")
            f.write(f"Web Interface: http://{esp32_ip}\n")
            f.write(f"Stream URL: {best_url}\n")
            f.write(f"\nConfig.py update:\n")
            f.write(f"CAMERA_INDEX = \"{best_url}\"\n")
        
        print(f"💾 Configuration saved to: esp32_stream_config.txt")
        
    else:
        print("⚠️ No OpenCV-compatible streams found")
        print("You may need to use image-based motion detection instead")
        
        if working_urls:
            jpeg_urls = [u['url'] for u in working_urls if u['type'] == 'jpeg_image']
            if jpeg_urls:
                print(f"📸 Try using JPEG URL: {jpeg_urls[0]}")
                print("This requires modifying the motion detection code for image polling")

if __name__ == "__main__":
    main()