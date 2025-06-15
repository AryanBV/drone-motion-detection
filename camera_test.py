#!/usr/bin/env python3
"""
Camera Test Script
Tests if your USB camera module works with OpenCV
"""

import cv2
import sys

def test_camera():
    """Test camera connection and display feed"""
    print("Testing camera connection...")
    
    # Try different camera indices (0, 1, 2...)
    for camera_index in range(3):
        print(f"Trying camera index {camera_index}...")
        
        # Create video capture object
        cap = cv2.VideoCapture(camera_index)
        
        # Check if camera opened successfully
        if not cap.isOpened():
            print(f"Camera {camera_index} not found")
            continue
            
        # Try to read a frame
        ret, frame = cap.read()
        if not ret:
            print(f"Camera {camera_index} found but cannot read frames")
            cap.release()
            continue
            
        print(f"SUCCESS! Camera {camera_index} is working")
        print(f"Resolution: {frame.shape[1]}x{frame.shape[0]}")
        
        # Display camera feed
        print("Displaying camera feed. Press 'q' to quit, 's' to save a test image")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to grab frame")
                break
                
            # Add text overlay
            cv2.putText(frame, f"Camera {camera_index} - Press 'q' to quit, 's' to save", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Display frame
            cv2.imshow('Camera Test', frame)
            
            # Check for key presses
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            elif key == ord('s'):
                # Save test image
                cv2.imwrite('test_image.jpg', frame)
                print("Test image saved as 'test_image.jpg'")
        
        # Clean up
        cap.release()
        cv2.destroyAllWindows()
        return camera_index
    
    print("ERROR: No working cameras found!")
    return None

if __name__ == "__main__":
    working_camera = test_camera()
    if working_camera is not None:
        print(f"\nYour camera is working on index {working_camera}")
        print("You can now proceed to motion detection!")
    else:
        print("\nPlease check your camera connection and try again.")
        sys.exit(1)