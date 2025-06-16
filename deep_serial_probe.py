#!/usr/bin/env python3
"""
Deep Serial Probe for ESP32-CAM
Extract all possible information about web server and URLs
"""

import serial
import time
import re

def deep_serial_investigation():
    """Comprehensive serial investigation"""
    print("🔍 Deep Serial Investigation")
    print("="*50)
    
    try:
        ser = serial.Serial("COM5", 115200, timeout=3)
        time.sleep(2)
        
        # Clear buffers
        ser.flushInput()
        ser.flushOutput()
        
        print("📡 Sending comprehensive commands...")
        
        # Comprehensive command list
        commands = [
            # Basic commands
            ("", "Basic test"),
            ("\r", "Carriage return"),
            ("\n", "Line feed"),
            ("?", "Help query"),
            ("help", "Help command"),
            ("menu", "Menu command"),
            
            # Web server commands
            ("server start", "Start server"),
            ("web start", "Start web"),
            ("http start", "Start HTTP"),
            ("camera start", "Start camera"),
            ("stream start", "Start stream"),
            
            # Status commands
            ("server status", "Server status"),
            ("web status", "Web status"),
            ("camera status", "Camera status"),
            ("network status", "Network status"),
            ("port", "Port info"),
            ("url", "URL info"),
            ("config", "Configuration"),
            
            # Arduino Serial Monitor commands
            ("Serial.println(\"test\")", "Arduino test"),
            ("WiFi.localIP()", "WiFi IP"),
            ("server.begin()", "Start server"),
            
            # AT Commands (if supported)
            ("AT", "AT test"),
            ("AT+HELP", "AT help"),
            ("AT+CIFSR", "Get IP"),
            ("AT+CIPSERVER?", "Server query"),
            ("AT+CIPSTART?", "Connection query"),
            
            # Custom commands that might exist
            ("ls", "List files"),
            ("dir", "Directory"),
            ("ps", "Process list"),
            ("netstat", "Network connections"),
            ("ifconfig", "Network interface"),
            
            # XIAO ESP32S3 specific
            ("xiao", "XIAO command"),
            ("esp32", "ESP32 command"),
            ("version", "Version info"),
            ("info", "Device info"),
            ("reset", "Reset command"),
        ]
        
        all_responses = []
        
        for cmd, description in commands:
            print(f"\n🔍 {description}: '{cmd}'")
            
            # Clear buffers
            ser.flushInput()
            ser.flushOutput()
            
            # Send command
            ser.write((cmd + '\r\n').encode())
            time.sleep(1.5)
            
            # Read response
            response = ""
            start_time = time.time()
            while time.time() - start_time < 2:
                if ser.in_waiting > 0:
                    new_data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                    response += new_data
                time.sleep(0.1)
            
            if response.strip():
                print(f"📥 Response: {response.strip()}")
                all_responses.append((cmd, response))
                
                # Look for URLs, ports, or server info
                url_patterns = [
                    r'http://[^\s]+',
                    r'https://[^\s]+', 
                    r'port\s*:?\s*(\d+)',
                    r'server\s*:?\s*(\d+)',
                    r'listening\s*:?\s*(\d+)',
                    r'bind\s*:?\s*(\d+)',
                    r'192\.168\.195\.193:(\d+)',
                    r'stream.*?(\d+)',
                    r'camera.*?(\d+)',
                ]
                
                for pattern in url_patterns:
                    matches = re.findall(pattern, response, re.IGNORECASE)
                    if matches:
                        print(f"🎯 Found pattern '{pattern}': {matches}")
            else:
                print("📥 No response")
        
        # Listen for spontaneous output
        print(f"\n📡 Listening for spontaneous output (15 seconds)...")
        start_time = time.time()
        spontaneous = ""
        
        while time.time() - start_time < 15:
            if ser.in_waiting > 0:
                new_data = ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
                spontaneous += new_data
                print(f"📨 Live: {new_data.strip()}")
            time.sleep(0.5)
        
        ser.close()
        
        # Analyze all responses
        print(f"\n" + "="*60)
        print(f"📊 COMPREHENSIVE ANALYSIS")
        print(f"="*60)
        
        # Combine all text
        all_text = " ".join([resp for cmd, resp in all_responses]) + " " + spontaneous
        
        # Look for port numbers
        port_patterns = [
            r':(\d+)',
            r'port\s*:?\s*(\d+)',
            r'server.*?(\d+)',
            r'listen.*?(\d+)',
        ]
        
        found_ports = set()
        for pattern in port_patterns:
            matches = re.findall(pattern, all_text, re.IGNORECASE)
            found_ports.update([int(p) for p in matches if p.isdigit() and 1 <= int(p) <= 65535])
        
        if found_ports:
            print(f"🔌 Potential ports found: {sorted(found_ports)}")
        else:
            print(f"❌ No port numbers found")
        
        # Look for URLs
        url_matches = re.findall(r'http://[^\s]+', all_text, re.IGNORECASE)
        if url_matches:
            print(f"🌐 URLs found: {url_matches}")
        else:
            print(f"❌ No URLs found")
        
        # Look for server/web indicators
        web_keywords = ['server', 'web', 'http', 'stream', 'camera', 'mjpeg', 'jpeg']
        found_web_keywords = [kw for kw in web_keywords if kw.lower() in all_text.lower()]
        
        if found_web_keywords:
            print(f"🌐 Web-related keywords: {found_web_keywords}")
        else:
            print(f"❌ No web server indicators found")
        
        return found_ports, url_matches, all_responses
        
    except Exception as e:
        print(f"❌ Serial investigation failed: {e}")
        return set(), [], []

def port_scan_esp32():
    """Scan specific ports on ESP32-CAM"""
    import socket
    
    ip = "192.168.195.193"
    
    # Common ESP32 ports
    ports_to_test = [
        80,    # Standard HTTP
        8080,  # Alternative HTTP
        8081,  # Alternative HTTP
        3000,  # Development server
        8000,  # Alternative web
        5000,  # Flask default
        81,    # ESP32 common alternative
        8888,  # Common alternative
        9090,  # Another common port
        443,   # HTTPS
        8443,  # Alternative HTTPS
        1883,  # MQTT (if used)
        8883,  # MQTT over SSL
    ]
    
    print(f"\n🔍 Port scanning {ip}...")
    open_ports = []
    
    for port in ports_to_test:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((ip, port))
            sock.close()
            
            if result == 0:
                print(f"   ✅ Port {port} is OPEN")
                open_ports.append(port)
            else:
                print(f"   ❌ Port {port} closed")
                
        except Exception as e:
            print(f"   ❌ Port {port} error: {e}")
    
    return open_ports

def test_open_ports(ip, ports):
    """Test HTTP on open ports"""
    import requests
    
    working_urls = []
    
    for port in ports:
        base_url = f"http://{ip}:{port}" if port != 80 else f"http://{ip}"
        
        endpoints = [
            "",
            "/",
            "/stream",
            "/video",
            "/cam-hi.jpg",
            "/capture",
            "/mjpeg",
        ]
        
        print(f"\n🔍 Testing HTTP on port {port}...")
        
        for endpoint in endpoints:
            url = base_url + endpoint
            try:
                print(f"   Testing: {url}")
                response = requests.get(url, timeout=3)
                
                if response.status_code == 200:
                    content_type = response.headers.get('content-type', '')
                    print(f"   ✅ SUCCESS: {url} - {content_type}")
                    working_urls.append({
                        'url': url,
                        'content_type': content_type,
                        'size': len(response.content)
                    })
                else:
                    print(f"   ❌ HTTP {response.status_code}: {url}")
                    
            except Exception as e:
                print(f"   ❌ Failed: {url} - {str(e)[:50]}")
    
    return working_urls

def main():
    print("🕵️ ESP32-CAM Deep Investigation Tool")
    print("="*60)
    
    # Step 1: Deep serial investigation
    found_ports, found_urls, responses = deep_serial_investigation()
    
    # Step 2: Port scanning
    print(f"\n🔍 Step 2: Port scanning...")
    open_ports = port_scan_esp32()
    
    # Combine found ports
    all_ports = found_ports.union(set(open_ports))
    
    if all_ports:
        print(f"\n✅ Found open ports: {sorted(all_ports)}")
        
        # Step 3: Test HTTP on open ports
        working_urls = test_open_ports("192.168.195.193", sorted(all_ports))
        
        if working_urls:
            print(f"\n🎉 WORKING URLs FOUND:")
            print(f"="*40)
            for url_info in working_urls:
                print(f"✅ {url_info['url']}")
                print(f"   Type: {url_info['content_type']}")
                print(f"   Size: {url_info['size']} bytes")
                print()
            
            # Save results
            with open("found_esp32_urls.txt", "w") as f:
                f.write("ESP32-CAM Working URLs\n")
                f.write("="*30 + "\n")
                for url_info in working_urls:
                    f.write(f"URL: {url_info['url']}\n")
                    f.write(f"Type: {url_info['content_type']}\n")
                    f.write(f"Size: {url_info['size']} bytes\n\n")
            
            print(f"💾 Results saved to: found_esp32_urls.txt")
            
            # Recommend best URL
            stream_urls = [u for u in working_urls if 'multipart' in u['content_type'] or 'mjpeg' in u['content_type']]
            image_urls = [u for u in working_urls if 'image/jpeg' in u['content_type']]
            
            if stream_urls:
                best = stream_urls[0]['url']
                print(f"\n🎯 RECOMMENDED for motion detection:")
                print(f"   CAMERA_INDEX = \"{best}\"")
            elif image_urls:
                best = image_urls[0]['url']
                print(f"\n🎯 ALTERNATIVE (image polling):")
                print(f"   CAMERA_INDEX = \"{best}\"")
                print(f"   (Note: This requires modified motion detection for image polling)")
        
        else:
            print(f"\n❌ No HTTP services found on open ports")
            print(f"🔧 This suggests the firmware doesn't have a web server")
    
    else:
        print(f"\n❌ No open ports found")
        print(f"🔧 Possible issues:")
        print(f"   1. Web server not running")
        print(f"   2. Firmware doesn't include web server")
        print(f"   3. Network connectivity issues")
        print(f"   4. Device not fully booted")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n👋 Investigation interrupted")
    except Exception as e:
        print(f"\n❌ Error: {e}")