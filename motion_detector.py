#!/usr/bin/env python3
"""
Optimized Motion Detection for ESP32-CAM
Enhanced for human detection with proper image saving including detection boxes
"""

import cv2
import numpy as np
import time
import os
import datetime
from config import *

class HumanOptimizedMotionDetector:
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
        self.human_detections = 0
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
                f.write(f"\n=== Human-Optimized Motion Detection Started at {datetime.datetime.now()} ===\n")
    
    def initialize_camera(self):
        """Initialize camera connection"""
        print(f"Initializing camera {CAMERA_INDEX}...")
        
        self.cap = cv2.VideoCapture(CAMERA_INDEX)
        if not self.cap.isOpened():
            raise Exception(f"Cannot open camera {CAMERA_INDEX}")
        
        print("Camera initialized successfully!")
        return True
    
    def preprocess_frame(self, frame):
        """Enhanced frame preprocessing for human detection"""
        # Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise while preserving human features
        blurred = cv2.GaussianBlur(gray, (GAUSSIAN_BLUR_SIZE, GAUSSIAN_BLUR_SIZE), 0)
        
        # Update lighting baseline for adaptive threshold
        if self.frame_count % 30 == 0:  # Update every 30 frames
            self.lighting_baseline = np.mean(blurred)
            
            if ADAPTIVE_THRESHOLD:
                # Adjust threshold based on lighting conditions
                if self.lighting_baseline < 50:  # Dark environment
                    self.current_threshold = MOTION_THRESHOLD + 15
                elif self.lighting_baseline > 200:  # Bright environment
                    self.current_threshold = MOTION_THRESHOLD + 10
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
    
    def merge_nearby_contours(self, contours):
        """Merge nearby contours to better detect complete human figures"""
        if not MERGE_NEARBY_CONTOURS or len(contours) <= 1:
            return contours
        
        # Convert contours to bounding rectangles for easier processing
        rectangles = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            rectangles.append((x, y, w, h, contour))
        
        merged_rectangles = []
        used = [False] * len(rectangles)
        
        for i, (x1, y1, w1, h1, contour1) in enumerate(rectangles):
            if used[i]:
                continue
                
            # Start with current rectangle
            min_x, min_y = x1, y1
            max_x, max_y = x1 + w1, y1 + h1
            merged_contours = [contour1]
            used[i] = True
            
            # Check all other rectangles for merging
            for j, (x2, y2, w2, h2, contour2) in enumerate(rectangles):
                if used[j]:
                    continue
                
                # Calculate distance between rectangles
                center1_x, center1_y = x1 + w1//2, y1 + h1//2
                center2_x, center2_y = x2 + w2//2, y2 + h2//2
                distance = np.sqrt((center1_x - center2_x)**2 + (center1_y - center2_y)**2)
                
                # Also check for overlap or proximity
                overlap_x = max(0, min(x1 + w1, x2 + w2) - max(x1, x2))
                overlap_y = max(0, min(y1 + h1, y2 + h2) - max(y1, y2))
                
                # Merge if close enough or overlapping
                if distance < CONTOUR_MERGE_DISTANCE or (overlap_x > 0 and overlap_y > 0):
                    min_x = min(min_x, x2)
                    min_y = min(min_y, y2)
                    max_x = max(max_x, x2 + w2)
                    max_y = max(max_y, y2 + h2)
                    merged_contours.append(contour2)
                    used[j] = True
            
            # Create merged contour from bounding rectangle
            if len(merged_contours) > 1 or cv2.contourArea(contour1) > MIN_CONTOUR_AREA:
                merged_contour = np.array([
                    [min_x, min_y],
                    [max_x, min_y],
                    [max_x, max_y],
                    [min_x, max_y]
                ])
                merged_rectangles.append(merged_contour)
        
        return merged_rectangles
    
    def detect_motion_enhanced(self, current_processed):
        """Enhanced motion detection optimized for humans"""
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
        
        # Enhanced morphological operations for human detection
        kernel = np.ones((MORPHOLOGY_KERNEL_SIZE, MORPHOLOGY_KERNEL_SIZE), np.uint8)
        
        # Opening removes noise
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        
        # Closing fills gaps in human silhouettes
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        # Light dilation to connect human body parts
        thresh = cv2.dilate(thresh, kernel, iterations=1)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by area
        motion_contours = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if MIN_CONTOUR_AREA <= area <= MAX_CONTOUR_AREA:
                motion_contours.append(contour)
        
        # Merge nearby contours for better human detection
        motion_contours = self.merge_nearby_contours(motion_contours)
        
        # Limit number of objects to reduce noise
        if len(motion_contours) > MAX_DETECTION_OBJECTS:
            # Keep the largest contours
            motion_contours = sorted(motion_contours, key=cv2.contourArea, reverse=True)[:MAX_DETECTION_OBJECTS]
        
        # Motion persistence check
        current_has_motion = len(motion_contours) > 0
        
        # Update motion history
        self.motion_history.append(current_has_motion)
        if len(self.motion_history) > MOTION_PERSISTENCE_FRAMES:
            self.motion_history.pop(0)
        
        # Check for persistent motion
        persistent_motion = False
        if len(self.motion_history) >= MOTION_PERSISTENCE_FRAMES:
            # Motion detected if it appears in most recent frames
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
    
    def log_motion_event(self, contour_count, total_motion_area, human_count):
        """Enhanced motion event logging"""
        if LOG_MOTION_EVENTS:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = (f"{timestamp} - VERIFIED Motion: {contour_count} objects "
                        f"({human_count} humans), total area: {total_motion_area}, "
                        f"threshold: {self.current_threshold}, avg_diff: {self.average_frame_diff:.1f}\n")
            
            with open(LOG_FILE, 'a') as f:
                f.write(log_entry)
    
    def save_motion_frame_with_detection(self, frame, contours, human_count):
        """Save frame with detection boxes and information overlay"""
        if SAVE_MOTION_FRAMES and contours:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = os.path.join(MOTION_FRAMES_DIR, f"motion_{timestamp}.jpg")
            
            # Create a copy for saving
            save_frame = frame.copy()
            
            if SAVE_WITH_DETECTION_BOXES:
                # Draw all contours with appropriate colors
                for contour in contours:
                    area = cv2.contourArea(contour)
                    x, y, w, h = cv2.boundingRect(contour)
                    
                    # Check if this is a human-sized contour
                    is_human = area >= MIN_HUMAN_AREA
                    
                    if is_human:
                        # Draw as human detection
                        cv2.rectangle(save_frame, (x, y), (x + w, y + h), HUMAN_BOX_COLOR, 3)
                        cv2.putText(save_frame, f"HUMAN: {int(area)}", (x, y - 10), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, HUMAN_BOX_COLOR, 2)
                    else:
                        # Draw as regular motion
                        cv2.rectangle(save_frame, (x, y), (x + w, y + h), MOTION_BOX_COLOR, 2)
                        cv2.putText(save_frame, f"Motion: {int(area)}", (x, y - 10), 
                                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, MOTION_BOX_COLOR, 1)
            
            if SAVE_DETECTION_INFO_ON_IMAGE:
                # Add detection summary
                info_y = 30
                cv2.putText(save_frame, "MOTION DETECTED", (10, info_y), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1, ALERT_TEXT_COLOR, 2)
                info_y += 40
                
                cv2.putText(save_frame, f"Objects: {len(contours)} | Humans: {human_count}", 
                           (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.7, ALERT_TEXT_COLOR, 2)
                info_y += 30
                
                cv2.putText(save_frame, f"Threshold: {self.current_threshold}", 
                           (10, info_y), cv2.FONT_HERSHEY_SIMPLEX, 0.6, INFO_TEXT_COLOR, 1)
                info_y += 25
                
                if ADD_TIMESTAMP_TO_SAVED_IMAGES:
                    cv2.putText(save_frame, timestamp, (10, save_frame.shape[0] - 20), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, INFO_TEXT_COLOR, 1)
            
            # Save the enhanced frame
            cv2.imwrite(filename, save_frame)
            
            if human_count > 0:
                print(f"🚨 Human motion saved with detection boxes: {filename}")
            else:
                print(f"📷 Motion saved with detection boxes: {filename}")
    
    def draw_enhanced_info(self, frame, contours, persistent_motion):
        """Draw enhanced motion detection information"""
        display_frame = frame.copy()
        
        # Draw contours only for persistent motion
        if SHOW_CONTOURS and persistent_motion:
            # Draw all contours with appropriate colors based on size
            for contour in contours:
                area = cv2.contourArea(contour)
                x, y, w, h = cv2.boundingRect(contour)
                
                # Check if this is a human-sized contour
                is_human = area >= MIN_HUMAN_AREA
                
                if is_human:
                    # Draw as human detection
                    cv2.rectangle(display_frame, (x, y), (x + w, y + h), HUMAN_BOX_COLOR, 3)
                    cv2.putText(display_frame, f"HUMAN: {int(area)}", (x, y - 10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, HUMAN_BOX_COLOR, 2)
                else:
                    # Draw as regular motion
                    cv2.rectangle(display_frame, (x, y), (x + w, y + h), MOTION_BOX_COLOR, 2)
                    cv2.putText(display_frame, f"Motion: {int(area)}", (x, y - 10), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.5, MOTION_BOX_COLOR, 1)
        
        # Motion status with human detection info
        human_count = len([c for c in contours if cv2.contourArea(c) >= MIN_HUMAN_AREA])
        
        if persistent_motion:
            if human_count > 0:
                status_text = f"HUMAN DETECTED! ({human_count})"
                status_color = (0, 100, 255)  # Orange for human
            else:
                status_text = "MOTION DETECTED!"
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
        
        cv2.putText(display_frame, f"Min Area: {MIN_CONTOUR_AREA} | Human: {MIN_HUMAN_AREA}", (10, info_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, DETECTION_STATS_COLOR, 1)
        info_y += line_height
        
        # Motion persistence info
        motion_count = sum(self.motion_history) if self.motion_history else 0
        cv2.putText(display_frame, f"Motion History: {motion_count}/{len(self.motion_history)}", (10, info_y), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, DETECTION_STATS_COLOR, 1)
        info_y += line_height
        
        # Detection statistics
        if SHOW_DETECTION_STATS:
            cv2.putText(display_frame, f"Total: {self.total_detections} | Humans: {self.human_detections}", (10, info_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, DETECTION_STATS_COLOR, 1)
            info_y += line_height
            
            cv2.putText(display_frame, f"Lighting: {self.lighting_baseline:.1f} | FrameDiff: {self.average_frame_diff:.1f}", (10, info_y), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, DETECTION_STATS_COLOR, 1)
        
        # Object count for verified motion
        if persistent_motion and contours:
            other_count = len([c for c in contours if cv2.contourArea(c) < MIN_HUMAN_AREA])
            count_text = f"Objects: {other_count} | Humans: {human_count}"
            cv2.putText(display_frame, count_text, (10, 45), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, ALERT_TEXT_COLOR, 2)
        
        # Instructions at bottom
        instructions = "Press: 'q'=quit, 's'=save, 'r'=reset, 't'=threshold"
        cv2.putText(display_frame, instructions, (10, frame.shape[0] - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, INFO_TEXT_COLOR, 1)
        
        return display_frame, human_count
    
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
            
            # Count human detections
            human_count = len([c for c in contours if cv2.contourArea(c) >= MIN_HUMAN_AREA])
            if human_count > 0:
                self.human_detections += 1
            
            total_motion_area = sum(cv2.contourArea(c) for c in contours)
            
            if human_count > 0:
                print(f"🚨 HUMAN DETECTED! Total objects: {len(contours)} | Humans: {human_count} | Area: {total_motion_area}")
            else:
                print(f"🚨 MOTION DETECTED! Objects: {len(contours)} | Area: {total_motion_area}")
            
            print(f"   Frame: {self.frame_count}, Threshold: {self.current_threshold}")
            
            # Log event
            self.log_motion_event(len(contours), total_motion_area, human_count)
            
            # Save frame with detection boxes - pass human_count instead of contour list
            self.save_motion_frame_with_detection(frame, contours, human_count)
        
        # Draw enhanced information
        display_frame, human_count = self.draw_enhanced_info(frame, contours, persistent_motion)
        
        # Show threshold image if enabled
        if SHOW_THRESHOLD_IMAGE and thresh is not None:
            thresh_colored = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
            cv2.putText(thresh_colored, f"Motion Analysis", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
            cv2.putText(thresh_colored, f"Threshold: {self.current_threshold}", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 1)
            cv2.imshow('Motion Analysis', thresh_colored)
        
        # Display main frame
        if WINDOW_SCALE != 1.0:
            height, width = display_frame.shape[:2]
            new_width = int(width * WINDOW_SCALE)
            new_height = int(height * WINDOW_SCALE)
            display_frame = cv2.resize(display_frame, (new_width, new_height))
        
        cv2.imshow('Human-Optimized Motion Detection', display_frame)
        
        return True
    
    def run(self):
        """Main execution loop with human detection features"""
        try:
            # Initialize camera
            self.initialize_camera()
            
            print("🎥 Human-Optimized Motion Detection Started!")
            print("=" * 60)
            print("✨ Human Detection Features:")
            print(f"   • Optimized for human movement detection")
            print(f"   • Saves images WITH detection boxes")
            print(f"   • Merges nearby contours for full human figures")
            print(f"   • Distinguishes humans from other motion")
            print(f"   • Motion Persistence: {MOTION_PERSISTENCE_FRAMES} frames")
            print(f"   • Human Area Threshold: {MIN_HUMAN_AREA}+ pixels")
            print()
            print("🎮 Controls:")
            print("   • 'q' - Quit detection")
            print("   • 's' - Save current frame manually")
            print("   • 'r' - Reset background manually")
            print("   • 't' - Toggle threshold view")
            print()
            print(f"⚙️ Optimized Settings:")
            print(f"   • Motion threshold: {MOTION_THRESHOLD} (adaptive)")
            print(f"   • Min area: {MIN_CONTOUR_AREA} | Human area: {MIN_HUMAN_AREA}")
            print(f"   • Persistence frames: {MOTION_PERSISTENCE_FRAMES}")
            print(f"   • Contour merging: {MERGE_NEARBY_CONTOURS}")
            
            show_threshold = SHOW_THRESHOLD_IMAGE
            
            while True:
                # Process motion detection
                if not self.process_motion_detection():
                    break
                
                # Handle key presses
                key = cv2.waitKey(1) & 0xFF
                if key == ord('q'):
                    print("Quitting human-optimized motion detection...")
                    break
                elif key == ord('s'):
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    ret, frame = self.cap.read()
                    if ret:
                        cv2.imwrite(f"manual_save_{timestamp}.jpg", frame)
                        print(f"Frame saved manually: manual_save_{timestamp}.jpg")
                elif key == ord('r'):
                    print("🔄 Manually resetting background...")
                    self.background_frame = None
                    self.prev_frame = None
                    self.motion_history = []
                    self.last_background_reset = time.time()
                elif key == ord('t'):
                    show_threshold = not show_threshold
                    if not show_threshold:
                        cv2.destroyWindow('Motion Analysis')
                    print(f"Threshold view: {'ON' if show_threshold else 'OFF'}")
                
        except KeyboardInterrupt:
            print("\nInterrupted by user")
        except Exception as e:
            print(f"Error: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Enhanced cleanup with human detection statistics"""
        if self.cap:
            self.cap.release()
        cv2.destroyAllWindows()
        
        # Print final statistics
        if self.frame_count > 0:
            detection_rate = (self.total_detections / self.frame_count) * 100
            human_rate = (self.human_detections / max(1, self.total_detections)) * 100
            
            print(f"\n📊 Final Statistics:")
            print(f"   Total Frames: {self.frame_count}")
            print(f"   Total Detections: {self.total_detections}")
            print(f"   Human Detections: {self.human_detections}")
            print(f"   Detection Rate: {detection_rate:.2f}%")
            print(f"   Human Detection Rate: {human_rate:.1f}% of all detections")
        
        if LOG_MOTION_EVENTS:
            with open(LOG_FILE, 'a') as f:
                f.write(f"=== Human-Optimized Motion Detection Ended at {datetime.datetime.now()} ===\n")
                f.write(f"Statistics: {self.frame_count} frames, {self.total_detections} detections, {self.human_detections} humans\n")
        
        print("Human-optimized cleanup completed")

def main():
    detector = HumanOptimizedMotionDetector()
    detector.run()

if __name__ == "__main__":
    main()