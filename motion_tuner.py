#!/usr/bin/env python3
"""
Real-Time Motion Detection Tuner
Adjust motion detection parameters while running to find optimal settings
"""

import cv2
import numpy as np
import time
import datetime

class MotionDetectionTuner:
    def __init__(self):
        self.stream_url = "http://192.168.1.5/sustain?stream=0"
        
        # Tunable parameters
        self.motion_threshold = 35
        self.min_contour_area = 1500
        self.gaussian_blur = 25
        self.morphology_size = 7
        self.show_threshold = True
        
        self.cap = None
        self.prev_frame = None
        self.frame_count = 0
        self.detection_count = 0
        self.last_detection_time = 0
        
    def initialize_camera(self):
        """Initialize camera connection"""
        print("🎥 Connecting to ESP32-CAM...")
        self.cap = cv2.VideoCapture(self.stream_url)
        
        if not self.cap.isOpened():
            print("❌ Failed to connect to camera")
            return False
        
        print("✅ Camera connected!")
        return True
    
    def create_control_window(self):
        """Create trackbars for real-time parameter adjustment"""
        cv2.namedWindow('Motion Controls')
        
        # Create trackbars
        cv2.createTrackbar('Threshold', 'Motion Controls', self.motion_threshold, 100, self.update_threshold)
        cv2.createTrackbar('Min Area', 'Motion Controls', int(self.min_contour_area/100), 50, self.update_min_area)
        cv2.createTrackbar('Blur Size', 'Motion Controls', self.gaussian_blur, 51, self.update_blur)
        cv2.createTrackbar('Morphology', 'Motion Controls', self.morphology_size, 20, self.update_morphology)
        cv2.createTrackbar('Show Threshold', 'Motion Controls', 1, 1, self.toggle_threshold)
        
        # Add instructions
        instructions = np.zeros((200, 600, 3), dtype=np.uint8)
        cv2.putText(instructions, "Motion Detection Tuner", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(instructions, "Use sliders to adjust parameters", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(instructions, "Threshold: Motion sensitivity", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.putText(instructions, "Min Area: Minimum motion size", (10, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.putText(instructions, "Blur Size: Noise reduction", (10, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.putText(instructions, "Morphology: Clean up detection", (10, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.putText(instructions, "Press 'q' to quit, 's' to save settings", (10, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 255), 1)
        
        cv2.imshow('Motion Controls', instructions)
    
    def update_threshold(self, val):
        self.motion_threshold = val
        print(f"📊 Threshold: {val}")
    
    def update_min_area(self, val):
        self.min_contour_area = val * 100
        print(f"📊 Min Area: {self.min_contour_area}")
    
    def update_blur(self, val):
        # Ensure odd number
        self.gaussian_blur = val if val % 2 == 1 else val + 1
        print(f"📊 Blur Size: {self.gaussian_blur}")
    
    def update_morphology(self, val):
        self.morphology_size = max(1, val)
        print(f"📊 Morphology: {self.morphology_size}")
    
    def toggle_threshold(self, val):
        self.show_threshold = bool(val)
    
    def process_frame(self):
        """Process a single frame for motion detection"""
        ret, frame = self.cap.read()
        if not ret:
            return False, None, None, []
        
        self.frame_count += 1
        
        # Preprocess frame
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (self.gaussian_blur, self.gaussian_blur), 0)
        
        # Motion detection
        if self.prev_frame is None:
            self.prev_frame = blurred.copy()
            return True, frame, None, []
        
        # Calculate difference
        frame_diff = cv2.absdiff(self.prev_frame, blurred)
        
        # Threshold
        _, thresh = cv2.threshold(frame_diff, self.motion_threshold, 255, cv2.THRESH_BINARY)
        
        # Morphological operations
        kernel = np.ones((self.morphology_size, self.morphology_size), np.uint8)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours
        motion_contours = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > self.min_contour_area:
                motion_contours.append(contour)
        
        # Update previous frame
        self.prev_frame = blurred.copy()
        
        return True, frame, thresh, motion_contours
    
    def draw_detection_info(self, frame, contours, thresh):
        """Draw detection information on frame"""
        display_frame = frame.copy()
        
        # Draw contours
        motion_detected = len(contours) > 0
        current_time = time.time()
        
        if motion_detected:
            self.detection_count += 1
            self.last_detection_time = current_time
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                area = cv2.contourArea(contour)
                cv2.putText(display_frame, f"Area: {int(area)}", (x, y - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # Status and parameters
        status = "MOTION DETECTED!" if motion_detected else "No Motion"
        color = (0, 0, 255) if motion_detected else (255, 255, 255)
        cv2.putText(display_frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
        
        # Current parameters
        cv2.putText(display_frame, f"Frame: {self.frame_count}", (10, 70), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(display_frame, f"Detections: {self.detection_count}", (10, 100), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        cv2.putText(display_frame, f"Threshold: {self.motion_threshold}", (10, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)
        cv2.putText(display_frame, f"Min Area: {self.min_contour_area}", (10, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)
        cv2.putText(display_frame, f"Objects: {len(contours)}", (10, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 1)
        
        # Detection rate
        if self.frame_count > 0:
            detection_rate = (self.detection_count / self.frame_count) * 100
            cv2.putText(display_frame, f"Detection Rate: {detection_rate:.1f}%", (10, 220), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 1)
        
        cv2.imshow('Motion Detection - Live Tuning', display_frame)
        
        # Show threshold image if enabled
        if self.show_threshold and thresh is not None:
            cv2.imshow('Threshold View', thresh)
        elif not self.show_threshold:
            cv2.destroyWindow('Threshold View')
    
    def save_settings(self):
        """Save current settings to file"""
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"motion_settings_{timestamp}.txt"
        
        with open(filename, 'w') as f:
            f.write("# Optimized Motion Detection Settings\n")
            f.write(f"# Generated: {datetime.datetime.now()}\n")
            f.write(f"# Detection Rate: {(self.detection_count / max(1, self.frame_count)) * 100:.1f}%\n")
            f.write(f"# Total Frames: {self.frame_count}\n")
            f.write(f"# Total Detections: {self.detection_count}\n\n")
            f.write(f"MOTION_THRESHOLD = {self.motion_threshold}\n")
            f.write(f"MIN_CONTOUR_AREA = {self.min_contour_area}\n")
            f.write(f"GAUSSIAN_BLUR_SIZE = {self.gaussian_blur}\n")
            f.write(f"MORPHOLOGY_KERNEL_SIZE = {self.morphology_size}\n")
        
        print(f"💾 Settings saved to: {filename}")
        
        # Also update config.py directly
        try:
            with open('config.py', 'r') as f:
                config_content = f.read()
            
            # Update values
            config_content = config_content.replace(f"MOTION_THRESHOLD = {35}", f"MOTION_THRESHOLD = {self.motion_threshold}")
            config_content = config_content.replace(f"MIN_CONTOUR_AREA = {1500}", f"MIN_CONTOUR_AREA = {self.min_contour_area}")
            config_content = config_content.replace(f"GAUSSIAN_BLUR_SIZE = {25}", f"GAUSSIAN_BLUR_SIZE = {self.gaussian_blur}")
            config_content = config_content.replace(f"MORPHOLOGY_KERNEL_SIZE = {7}", f"MORPHOLOGY_KERNEL_SIZE = {self.morphology_size}")
            
            with open('config.py', 'w') as f:
                f.write(config_content)
            
            print("✅ config.py updated with new settings!")
            
        except Exception as e:
            print(f"⚠️ Could not update config.py: {e}")
    
    def run(self):
        """Main tuning loop"""
        if not self.initialize_camera():
            return
        
        self.create_control_window()
        
        print("🎛️ Motion Detection Tuner Started")
        print("=" * 50)
        print("📊 Use the sliders to adjust parameters in real-time")
        print("🎯 Goal: Detect intentional motion, ignore lighting/noise")
        print("💡 Tips:")
        print("   - Lower threshold = more sensitive")
        print("   - Higher min area = ignore small movements") 
        print("   - Higher blur = less noise sensitivity")
        print("📝 Press 's' to save optimal settings")
        print("❌ Press 'q' to quit")
        
        try:
            while True:
                success, frame, thresh, contours = self.process_frame()
                
                if not success:
                    print("❌ Failed to read frame")
                    break
                
                self.draw_detection_info(frame, contours, thresh)
                
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    break
                elif key == ord('s'):
                    self.save_settings()
                elif key == ord('r'):
                    print("🔄 Reset background")
                    self.prev_frame = None
                
        except KeyboardInterrupt:
            print("\n⏹️ Tuning stopped")
        
        finally:
            if self.cap:
                self.cap.release()
            cv2.destroyAllWindows()
            
            # Print final stats
            if self.frame_count > 0:
                detection_rate = (self.detection_count / self.frame_count) * 100
                print(f"\n📊 Final Statistics:")
                print(f"   Frames Processed: {self.frame_count}")
                print(f"   Motion Detections: {self.detection_count}")
                print(f"   Detection Rate: {detection_rate:.1f}%")
                print(f"   Final Settings:")
                print(f"     Threshold: {self.motion_threshold}")
                print(f"     Min Area: {self.min_contour_area}")
                print(f"     Blur Size: {self.gaussian_blur}")
                print(f"     Morphology: {self.morphology_size}")

if __name__ == "__main__":
    tuner = MotionDetectionTuner()
    tuner.run()