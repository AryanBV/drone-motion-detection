#!/usr/bin/env python3
"""
Motion Detection Script for Drone Camera
Detects motion using frame differencing and alerts when motion is detected
"""

import cv2
import numpy as np
import time
import os
import datetime
from config import *

class MotionDetector:
    def __init__(self):
        self.cap = None
        self.prev_frame = None
        self.current_frame = None
        self.motion_detected = False
        self.last_motion_time = 0
        self.frame_count = 0
        
        # Create directories
        if SAVE_MOTION_FRAMES and not os.path.exists(MOTION_FRAMES_DIR):
            os.makedirs(MOTION_FRAMES_DIR)
            
        # Initialize logging
        if LOG_MOTION_EVENTS:
            with open(LOG_FILE, 'a') as f:
                f.write(f"\n=== Motion Detection Started at {datetime.datetime.now()} ===\n")
    
    def initialize_camera(self):
        """Initialize camera connection"""
        print(f"Initializing camera {CAMERA_INDEX}...")
        
        self.cap = cv2.VideoCapture(CAMERA_INDEX)
        if not self.cap.isOpened():
            raise Exception(f"Cannot open camera {CAMERA_INDEX}")
        
        # Set camera properties
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
        self.cap.set(cv2.CAP_PROP_FPS, FPS)
        
        print("Camera initialized successfully!")
        return True
    
    def preprocess_frame(self, frame):
        """Preprocess frame for motion detection"""
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (GAUSSIAN_BLUR_SIZE, GAUSSIAN_BLUR_SIZE), 0)
        
        return blurred
    
    def detect_motion_frame_diff(self, current_processed, prev_processed):
        """Detect motion using frame differencing"""
        if prev_processed is None:
            return None, []
        
        # Calculate absolute difference between frames
        frame_diff = cv2.absdiff(prev_processed, current_processed)
        
        # Apply threshold to get binary image
        _, thresh = cv2.threshold(frame_diff, MOTION_THRESHOLD, 255, cv2.THRESH_BINARY)
        
        # Apply morphological operations to reduce noise
        kernel = np.ones((MORPHOLOGY_KERNEL_SIZE, MORPHOLOGY_KERNEL_SIZE), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by area
        motion_contours = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if MIN_CONTOUR_AREA <= area <= MAX_CONTOUR_AREA:
                motion_contours.append(contour)
        
        return thresh, motion_contours
    
    def log_motion_event(self, contour_count, total_motion_area):
        """Log motion detection event"""
        if LOG_MOTION_EVENTS:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"{timestamp} - Motion detected: {contour_count} objects, total area: {total_motion_area}\n"
            
            with open(LOG_FILE, 'a') as f:
                f.write(log_entry)
    
    def save_motion_frame(self, frame, contours):
        """Save frame when motion is detected"""
        if SAVE_MOTION_FRAMES and contours:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = os.path.join(MOTION_FRAMES_DIR, f"motion_{timestamp}.jpg")
            cv2.imwrite(filename, frame)
            print(f"Motion frame saved: {filename}")
    
    def draw_motion_info(self, frame, contours, motion_detected):
        """Draw motion detection information on frame"""
        # Draw bounding boxes around motion
        if SHOW_CONTOURS and contours:
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(frame, (x, y), (x + w, y + h), MOTION_BOX_COLOR, 2)
                
                # Draw area text
                area = cv2.contourArea(contour)
                cv2.putText(frame, f"Area: {int(area)}", (x, y - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, MOTION_BOX_COLOR, 1)
        
        # Draw motion status
        status_text = "MOTION DETECTED!" if motion_detected else "No Motion"
        status_color = ALERT_TEXT_COLOR if motion_detected else INFO_TEXT_COLOR
        cv2.putText(frame, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, status_color, 2)
        
        # Draw frame counter and settings info
        info_text = f"Frame: {self.frame_count} | Threshold: {MOTION_THRESHOLD} | Min Area: {MIN_CONTOUR_AREA}"
        cv2.putText(frame, info_text, (10, frame.shape[0] - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, INFO_TEXT_COLOR, 1)
        
        # Draw object count
        if contours:
            count_text = f"Objects detected: {len(contours)}"
            cv2.putText(frame, count_text, (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, ALERT_TEXT_COLOR, 2)
        
        return frame
    
    def process_motion_detection(self):
        """Main motion detection processing"""
        current_time = time.time()
        
        # Read frame
        ret, frame = self.cap.read()
        if not ret:
            print("Failed to read frame")
            return False
        
        self.frame_count += 1
        
        # Preprocess current frame
        current_processed = self.preprocess_frame(frame)
        
        # Detect motion
        thresh, contours = self.detect_motion_frame_diff(current_processed, self.prev_frame)
        
        # Check if motion detected
        motion_detected = len(contours) > 0
        
        # Handle motion detection
        if motion_detected and (current_time - self.last_motion_time) > MOTION_ALERT_COOLDOWN:
            self.last_motion_time = current_time
            total_motion_area = sum(cv2.contourArea(c) for c in contours)
            
            print(f"🚨 MOTION DETECTED! Objects: {len(contours)}, Total Area: {total_motion_area}")
            
            # Log event
            self.log_motion_event(len(contours), total_motion_area)
            
            # Save frame
            self.save_motion_frame(frame, contours)
            
            # Here you could add drone communication
            # Example: send_alert_to_drone()
        
        # Draw information on frame
        display_frame = self.draw_motion_info(frame.copy(), contours, motion_detected)
        
        # Show threshold image if enabled
        if SHOW_THRESHOLD_IMAGE and thresh is not None:
            cv2.imshow('Motion Threshold', thresh)
        
        # Display main frame
        if WINDOW_SCALE != 1.0:
            height, width = display_frame.shape[:2]
            new_width = int(width * WINDOW_SCALE)
            new_height = int(height * WINDOW_SCALE)
            display_frame = cv2.resize(display_frame, (new_width, new_height))
        
        cv2.imshow('Motion Detection', display_frame)
        
        # Update previous frame
        self.prev_frame = current_processed.copy()
        
        return True
    
    def run(self):
        """Main execution loop"""
        try:
            # Initialize camera
            self.initialize_camera()
            
            print("Motion detection started!")
            print("Press 'q' to quit, 's' to save current frame, 'r' to reset background")
            print(f"Motion threshold: {MOTION_THRESHOLD}, Min area: {MIN_CONTOUR_AREA}")
            
            while True:
                # Process motion detection
                if not self.process_motion_detection():
                    break
                
                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("Quitting motion detection...")
                    break
                elif key == ord('s'):
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    ret, frame = self.cap.read()
                    if ret:
                        cv2.imwrite(f"manual_save_{timestamp}.jpg", frame)
                        print(f"Frame saved: manual_save_{timestamp}.jpg")
                elif key == ord('r'):
                    print("Resetting background...")
                    self.prev_frame = None
                
        except KeyboardInterrupt:
            print("\nInterrupted by user")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources"""
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        
        if LOG_MOTION_EVENTS:
            with open(LOG_FILE, 'a') as f:
                f.write(f"=== Motion Detection Ended at {datetime.datetime.now()} ===\n")
        
        print("Cleanup completed")

def main():
    detector = MotionDetector()
    detector.run()

if __name__ == "__main__":
    main()