#!/usr/bin/env python3
"""
Improved Motion Detection Script for ESP32-CAM
Enhanced with motion persistence, adaptive thresholding, and stability improvements
"""

import cv2
import numpy as np
import time
import os
import datetime
from config import *

class ImprovedMotionDetector:
    def __init__(self):
        self.cap = None
        self.prev_frame = None
        self.background_frame = None
        self.motion_detected = False
        self.last_motion_time = 0
        self.frame_count = 0
        self.last_background_reset = time.time()
        
        # Motion persistence tracking
        self.motion_history = []
        self.consecutive_motion_frames = 0
        
        # Detection statistics
        self.total_detections = 0
        self.false_positive_reduction = 0
        self.average_frame_diff = 0
        
        # Adaptive threshold
        self.current_threshold = MOTION_THRESHOLD
        self.lighting_baseline = 0
        
        # Create directories
        if SAVE_MOTION_FRAMES and not os.path.exists(MOTION_FRAMES_DIR):
            os.makedirs(MOTION_FRAMES_DIR)
            
        # Initialize logging
        if LOG_MOTION_EVENTS:
            with open(LOG_FILE, 'a') as f:
                f.write(f"\n=== Enhanced Motion Detection Started at {datetime.datetime.now()} ===\n")
    
    def initialize_camera(self):
        """Initialize camera connection"""
        print(f"Initializing camera {CAMERA_INDEX}...")
        
        self.cap = cv2.VideoCapture(CAMERA_INDEX)
        if not self.cap.isOpened():
            raise Exception(f"Cannot open camera {CAMERA_INDEX}")
        
        # Set camera properties (may not work with network streams)
        try:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, CAMERA_WIDTH)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, CAMERA_HEIGHT)
            self.cap.set(cv2.CAP_PROP_FPS, FPS)
        except:
            pass  # Network streams don't always support property setting
        
        print("Camera initialized successfully!")
        return True
    
    def preprocess_frame(self, frame):
        """Enhanced frame preprocessing"""
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (GAUSSIAN_BLUR_SIZE, GAUSSIAN_BLUR_SIZE), 0)
        
        # Update lighting baseline for adaptive threshold
        if self.frame_count % 30 == 0:  # Update every 30 frames
            self.lighting_baseline = np.mean(blurred)
            
            if ADAPTIVE_THRESHOLD:
                # Adjust threshold based on lighting conditions
                if self.lighting_baseline < 50:  # Dark environment
                    self.current_threshold = MOTION_THRESHOLD + 10
                elif self.lighting_baseline > 200:  # Bright environment
                    self.current_threshold = MOTION_THRESHOLD + 20
                else:
                    self.current_threshold = MOTION_THRESHOLD
        
        return blurred
    
    def update_background(self, current_frame, learning_rate=None):
        """Update background model with current frame"""
        if learning_rate is None:
            learning_rate = BACKGROUND_UPDATE_RATE
            
        if self.background_frame is None:
            self.background_frame = current_frame.copy().astype(np.float32)
        else:
            # Slowly update background
            cv2.accumulateWeighted(current_frame, self.background_frame, learning_rate)
    
    def detect_motion_enhanced(self, current_processed):
        """Enhanced motion detection with persistence"""
        if self.prev_frame is None:
            self.prev_frame = current_processed.copy()
            self.update_background(current_processed)
            return None, [], False
        
        # Calculate frame difference
        frame_diff = cv2.absdiff(self.prev_frame, current_processed)
        
        # Calculate average difference for statistics
        self.average_frame_diff = np.mean(frame_diff)
        
        # Apply adaptive threshold
        _, thresh = cv2.threshold(frame_diff, self.current_threshold, 255, cv2.THRESH_BINARY)
        
        # Enhanced morphological operations
        kernel = np.ones((MORPHOLOGY_KERNEL_SIZE, MORPHOLOGY_KERNEL_SIZE), np.uint8)
        
        # Opening removes noise
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        
        # Closing fills gaps
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        # Additional dilation for better contour detection
        thresh = cv2.dilate(thresh, kernel, iterations=2)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by area
        motion_contours = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if MIN_CONTOUR_AREA <= area <= MAX_CONTOUR_AREA:
                motion_contours.append(contour)
        
        # Motion persistence check
        current_has_motion = len(motion_contours) > 0
        
        # Update motion history
        self.motion_history.append(current_has_motion)
        if len(self.motion_history) > MOTION_PERSISTENCE_FRAMES:
            self.motion_history.pop(0)
        
        # Check for persistent motion
        persistent_motion = False
        if len(self.motion_history) >= MOTION_PERSISTENCE_FRAMES:
            # Motion detected if it appears in at least X of the last Y frames
            motion_count = sum(self.motion_history)
            persistent_motion = motion_count >= (MOTION_PERSISTENCE_FRAMES - 1)
        
        # Update consecutive motion counter
        if current_has_motion:
            self.consecutive_motion_frames += 1
        else:
            self.consecutive_motion_frames = 0
        
        # Update background when no motion
        if not current_has_motion:
            self.update_background(current_processed)
        elif self.consecutive_motion_frames < 10:  # Update even with small motion
            self.update_background(current_processed, learning_rate=0.001)
        
        # Update previous frame
        self.prev_frame = current_processed.copy()
        
        return thresh, motion_contours, persistent_motion
    
    def auto_reset_background(self):
        """Automatically reset background periodically"""
        current_time = time.time()
        if AUTO_RESET_BACKGROUND and (current_time - self.last_background_reset) > RESET_BACKGROUND_INTERVAL:
            print("🔄 Auto-resetting background...")
            self.background_frame = None
            self.prev_frame = None
            self.motion_history = []
            self.last_background_reset = current_time
    
    def log_motion_event(self, contour_count, total_motion_area):
        """Enhanced motion event logging"""
        if LOG_MOTION_EVENTS:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = (f"{timestamp} - VERIFIED Motion: {contour_count} objects, "
                        f"total area: {total_motion_area}, threshold: {self.current_threshold}, "
                        f"avg_diff: {self.average_frame_diff:.1f}\n")
            
            with open(LOG_FILE, 'a') as f:
                f.write(log_entry)
    
    def save_motion_frame(self, frame, contours):
        """Save frame when verified motion is detected"""
        if SAVE_MOTION_FRAMES and contours:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = os.path.join(MOTION_FRAMES_DIR, f"verified_motion_{timestamp}.jpg")
            cv2.imwrite(filename, frame)
            print(f"Verified motion frame saved: {filename}")
    
    def draw_enhanced_info(self, frame, contours, persistent_motion):
        """Draw enhanced motion detection information"""
        display_frame = frame.copy()
        
        # Draw contours only for persistent motion
        if SHOW_CONTOURS and persistent_motion and contours:
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                cv2.rectangle(display_frame, (x, y), (x + w, y + h), MOTION_BOX_COLOR, 3)
                
                # Draw area text
                area = cv2.contourArea(contour)
                cv2.putText(display_frame, f"Area: {int(area)}", (x, y - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, MOTION_BOX_COLOR, 2)
        
        # Motion status
        if persistent_motion:
            status_text = "VERIFIED MOTION!"
            status_color = ALERT_TEXT_COLOR
        else:
            status_text = "No Motion"
            status_color = INFO_TEXT_COLOR
        
        cv2.putText(display_frame, status_text, (10, 35), cv2.FONT_HERSHEY_SIMPLEX, 1.2, status_color, 3)
        
        # Enhanced information display
        info_y = 70
        line_height = 25
        
        # Frame and detection info
        cv2.putText(display_frame, f"Frame: {self.frame_count}", (10, info_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, INFO_TEXT_COLOR, 1)
        info_y += line_height
        
        cv2.putText(display_frame, f"Threshold: {self.current_threshold} (adaptive)", (10, info_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, DETECTION_STATS_COLOR, 1)
        info_y += line_height
        
        cv2.putText(display_frame, f"Min Area: {MIN_CONTOUR_AREA}", (10, info_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, DETECTION_STATS_COLOR, 1)
        info_y += line_height
        
        # Motion persistence info
        motion_count = sum(self.motion_history) if self.motion_history else 0
        cv2.putText(display_frame, f"Motion History: {motion_count}/{len(self.motion_history)}", (10, info_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, DETECTION_STATS_COLOR, 1)
        info_y += line_height
        
        # Detection statistics
        if SHOW_DETECTION_STATS:
            cv2.putText(display_frame, f"Avg Frame Diff: {self.average_frame_diff:.1f}", (10, info_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, DETECTION_STATS_COLOR, 1)
            info_y += line_height
            
            cv2.putText(display_frame, f"Lighting: {self.lighting_baseline:.1f}", (10, info_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, DETECTION_STATS_COLOR, 1)
            info_y += line_height
            
            cv2.putText(display_frame, f"Total Verified: {self.total_detections}", (10, info_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, DETECTION_STATS_COLOR, 1)
        
        # Object count for verified motion
        if persistent_motion and contours:
            count_text = f"Verified Objects: {len(contours)}"
            cv2.putText(display_frame, count_text, (10, 45), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, ALERT_TEXT_COLOR, 2)
        
        # Instructions at bottom
        instructions = "Press: 'q'=quit, 's'=save, 'r'=reset background"
        cv2.putText(display_frame, instructions, (10, frame.shape[0] - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, INFO_TEXT_COLOR, 1)
        
        return display_frame
    
    def process_motion_detection(self):
        """Enhanced motion detection processing"""
        current_time = time.time()
        
        # Read frame
        ret, frame = self.cap.read()
        if not ret:
            print("Failed to read frame")
            return False
        
        self.frame_count += 1
        
        # Auto-reset background periodically
        self.auto_reset_background()
        
        # Preprocess current frame
        current_processed = self.preprocess_frame(frame)
        
        # Enhanced motion detection
        thresh, contours, persistent_motion = self.detect_motion_enhanced(current_processed)
        
        # Handle verified motion detection
        if persistent_motion and (current_time - self.last_motion_time) > MOTION_ALERT_COOLDOWN:
            self.last_motion_time = current_time
            self.total_detections += 1
            total_motion_area = sum(cv2.contourArea(c) for c in contours)
            
            print(f"🚨 VERIFIED MOTION! Objects: {len(contours)}, Total Area: {total_motion_area}")
            print(f"   Frame: {self.frame_count}, Threshold: {self.current_threshold}")
            
            # Log event
            self.log_motion_event(len(contours), total_motion_area)
            
            # Save frame
            self.save_motion_frame(frame, contours)
            
            # Here you could add drone communication
            # Example: send_alert_to_drone()
        
        # Draw enhanced information
        display_frame = self.draw_enhanced_info(frame, contours, persistent_motion)
        
        # Show threshold image if enabled
        if SHOW_THRESHOLD_IMAGE and thresh is not None:
            # Add info to threshold image
            thresh_colored = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
            cv2.putText(thresh_colored, f"Motion Threshold View", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(thresh_colored, f"Threshold: {self.current_threshold}", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)
            cv2.imshow('Motion Threshold', thresh_colored)
        
        # Display main frame
        if WINDOW_SCALE != 1.0:
            height, width = display_frame.shape[:2]
            new_width = int(width * WINDOW_SCALE)
            new_height = int(height * WINDOW_SCALE)
            display_frame = cv2.resize(display_frame, (new_width, new_height))
        
        cv2.imshow('Enhanced Motion Detection', display_frame)
        
        return True
    
    def run(self):
        """Main execution loop with enhanced features"""
        try:
            # Initialize camera
            self.initialize_camera()
            
            print("🎥 Enhanced Motion Detection Started!")
            print("=" * 60)
            print("✨ New Features:")
            print(f"   • Motion Persistence: {MOTION_PERSISTENCE_FRAMES} frames required")
            print(f"   • Adaptive Threshold: {ADAPTIVE_THRESHOLD}")
            print(f"   • Auto Background Reset: {AUTO_RESET_BACKGROUND}")
            print(f"   • Enhanced Noise Filtering")
            print()
            print("🎮 Controls:")
            print("   • 'q' - Quit detection")
            print("   • 's' - Save current frame")
            print("   • 'r' - Reset background manually")
            print("   • 't' - Toggle threshold view")
            print()
            print(f"⚙️ Settings:")
            print(f"   • Motion threshold: {MOTION_THRESHOLD} (adaptive)")
            print(f"   • Min area: {MIN_CONTOUR_AREA}")
            print(f"   • Persistence frames: {MOTION_PERSISTENCE_FRAMES}")
            
            show_threshold = SHOW_THRESHOLD_IMAGE
            
            while True:
                # Process motion detection
                if not self.process_motion_detection():
                    break
                
                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("Quitting enhanced motion detection...")
                    break
                elif key == ord('s'):
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    ret, frame = self.cap.read()
                    if ret:
                        cv2.imwrite(f"manual_save_{timestamp}.jpg", frame)
                        print(f"Frame saved: manual_save_{timestamp}.jpg")
                elif key == ord('r'):
                    print("🔄 Manually resetting background...")
                    self.background_frame = None
                    self.prev_frame = None
                    self.motion_history = []
                    self.last_background_reset = time.time()
                elif key == ord('t'):
                    show_threshold = not show_threshold
                    if not show_threshold:
                        cv2.destroyWindow('Motion Threshold')
                    print(f"Threshold view: {'ON' if show_threshold else 'OFF'}")
                
        except KeyboardInterrupt:
            print("\nInterrupted by user")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Enhanced cleanup with statistics"""
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        
        # Print final statistics
        if self.frame_count > 0:
            detection_rate = (self.total_detections / self.frame_count) * 100
            print(f"\n📊 Final Statistics:")
            print(f"   Total Frames: {self.frame_count}")
            print(f"   Verified Detections: {self.total_detections}")
            print(f"   Detection Rate: {detection_rate:.2f}%")
        
        if LOG_MOTION_EVENTS:
            with open(LOG_FILE, 'a') as f:
                f.write(f"=== Enhanced Motion Detection Ended at {datetime.datetime.now()} ===\n")
                f.write(f"Statistics: {self.frame_count} frames, {self.total_detections} verified detections\n")
        
        print("Enhanced cleanup completed")

def main():
    detector = ImprovedMotionDetector()
    detector.run()

if __name__ == "__main__":
    main()