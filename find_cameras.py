#!/usr/bin/env python3
"""
Enhanced Camera Detection Script
Finds all available cameras and shows detailed information
"""

import cv2
import time

def get_camera_info(index):
    """Get detailed information about a camera"""
    cap = cv2.VideoCapture(index)
    
    if not cap.isOpened():
        return None
    
    # Try to read a frame
    ret, frame = cap.read()
    if not ret:
        cap.release()
        return None
    
    # Get camera properties
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    backend = cap.get(cv2.CAP_PROP_BACKEND)
    
    # Try to get more properties
    brightness = cap.get(cv2.CAP_PROP_BRIGHTNESS)
    contrast = cap.get(cv2.CAP_PROP_CONTRAST)
    saturation = cap.get(cv2.CAP_PROP_SATURATION)
    
    info = {
        'index': index,
        'resolution': f"{width}x{height}",
        'fps': fps,
        'backend': backend,
        'brightness': brightness,
        'contrast': contrast,
        'saturation': saturation,
        'frame_shape': frame.shape if frame is not None else None
    }
    
    cap.release()
    return info

def test_camera_with_preview(index):
    """Test a specific camera with live preview"""
    print(f"\n=== Testing Camera {index} ===")
    
    cap = cv2.VideoCapture(index)
    if not cap.isOpened():
        print(f"Camera {index}: Cannot open")
        return False
    
    # Get initial frame
    ret, frame = cap.read()
    if not ret:
        print(f"Camera {index}: Cannot read frames")
        cap.release()
        return False
    
    print(f"Camera {index}: Working!")
    print(f"Resolution: {frame.shape[1]}x{frame.shape[0]}")
    print(f"Press SPACE to test this camera, 'n' for next camera, 'q' to quit")
    
    # Show preview for 3 seconds
    start_time = time.time()
    while time.time() - start_time < 3:
        ret, frame = cap.read()
        if ret:
            # Add text overlay
            cv2.putText(frame, f"Camera {index} Preview", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, "Press SPACE to test, 'n' for next", (10, 70), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            cv2.imshow(f'Camera {index} Preview', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord(' '):
                # Full test of this camera
                print(f"Testing Camera {index} - Press 'q' to finish test")
                test_full_camera(cap, index)
                cap.release()
                cv2.destroyAllWindows()
                return True
            elif key == ord('n'):
                break
            elif key == ord('q'):
                cap.release()
                cv2.destroyAllWindows()
                return False
    
    cap.release()
    cv2.destroyAllWindows()
    return False

def test_full_camera(cap, index):
    """Full test of a camera with controls"""
    print(f"Full test of Camera {index}")
    print("Controls: 'q' quit, 's' save image, 'i' show info")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Cannot read frame")
            break
        
        # Add comprehensive overlay
        cv2.putText(frame, f"Camera {index} - Full Test", (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, f"Resolution: {frame.shape[1]}x{frame.shape[0]}", (10, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, "Press 'q' to quit, 's' to save", (10, 110), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        cv2.imshow(f'Camera {index} Full Test', frame)
        
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('s'):
            filename = f"camera_{index}_test.jpg"
            cv2.imwrite(filename, frame)
            print(f"Image saved: {filename}")
        elif key == ord('i'):
            info = get_camera_info(index)
            if info:
                print(f"Camera {index} Info:")
                for key, value in info.items():
                    print(f"  {key}: {value}")

def main():
    print("🔍 Enhanced Camera Detection")
    print("=" * 50)
    
    # First, scan all cameras
    print("Scanning for cameras...")
    available_cameras = []
    
    for i in range(10):  # Check first 10 camera indices
        info = get_camera_info(i)
        if info:
            available_cameras.append(info)
            print(f"✅ Camera {i}: {info['resolution']} - Backend: {info['backend']}")
        else:
            print(f"❌ Camera {i}: Not available")
    
    if not available_cameras:
        print("\n❌ No cameras found!")
        return
    
    print(f"\n✅ Found {len(available_cameras)} camera(s)")
    print("\nCamera Details:")
    print("-" * 50)
    
    for info in available_cameras:
        print(f"Camera {info['index']}:")
        print(f"  Resolution: {info['resolution']}")
        print(f"  FPS: {info['fps']}")
        print(f"  Backend: {info['backend']}")
        print(f"  Frame shape: {info['frame_shape']}")
        print()
    
    # Now test each camera with preview
    print("Testing cameras with preview...")
    print("=" * 50)
    
    for info in available_cameras:
        if test_camera_with_preview(info['index']):
            # User selected this camera
            print(f"\n✅ Camera {info['index']} selected!")
            print(f"Update your config.py: CAMERA_INDEX = {info['index']}")
            return
    
    print("\nNo camera selected. Check the output above to identify your USB camera.")
    print("Look for a camera that:")
    print("- Has a resolution matching your USB camera specs")
    print("- Is NOT labeled as 'Virtual Camera' or 'OBS'")
    print("- Shows actual video feed from your USB camera")

if __name__ == "__main__":
    main()