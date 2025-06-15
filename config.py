#!/usr/bin/env python3
"""
Improved Configuration for ESP32-CAM Motion Detection
Optimized to eliminate false positives while maintaining good sensitivity
"""

# Camera Settings - ESP32-CAM Stream
CAMERA_INDEX = "http://192.168.1.5/sustain?stream=0"
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
FPS = 30

# Motion Detection Settings - OPTIMIZED FOR STABILITY
MOTION_THRESHOLD = 50          # Increased from 35 - less sensitive to lighting changes
MIN_CONTOUR_AREA = 2500        # Increased from 1500 - ignore small movements
MAX_CONTOUR_AREA = 50000       # Keep large movements

# Frame Processing - ENHANCED NOISE REDUCTION
GAUSSIAN_BLUR_SIZE = 31        # Increased from 25 for better noise filtering
MORPHOLOGY_KERNEL_SIZE = 9     # Increased from 7 for better cleanup

# Motion Persistence Settings - NEW FEATURES
MOTION_PERSISTENCE_FRAMES = 3   # Motion must be detected in X consecutive frames
BACKGROUND_UPDATE_RATE = 0.01   # How fast background adapts (lower = slower)

# Alert Settings
MOTION_ALERT_COOLDOWN = 4.0    # Increased from 3.0 to reduce alert spam
SAVE_MOTION_FRAMES = True
MOTION_FRAMES_DIR = "motion_frames"

# Display Settings
SHOW_THRESHOLD_IMAGE = True    # Shows what the detector sees
SHOW_CONTOURS = True           # Draw green boxes around motion
WINDOW_SCALE = 1.0             # Display scale factor

# Colors (BGR format)
MOTION_BOX_COLOR = (0, 255, 0)     # Green boxes around motion
ALERT_TEXT_COLOR = (0, 0, 255)     # Red text for alerts
INFO_TEXT_COLOR = (255, 255, 255)  # White text for info
DETECTION_STATS_COLOR = (0, 255, 255)  # Yellow for detection stats

# Logging
LOG_MOTION_EVENTS = True
LOG_FILE = "motion_log.txt"

# Advanced Settings
BACKGROUND_SUBTRACTION_HISTORY = 500
BACKGROUND_SUBTRACTION_THRESHOLD = 50
MOTION_DETECTION_METHOD = "frame_diff"

# Sensitivity Control - FINE TUNING
AUTO_RESET_BACKGROUND = True    # Automatically reset background periodically
RESET_BACKGROUND_INTERVAL = 300 # Reset background every 5 minutes (300 seconds)
ADAPTIVE_THRESHOLD = True       # Adjust threshold based on lighting conditions

# Future Integration Settings (for drone communication)
DRONE_COMMUNICATION = False
DRONE_IP = "192.168.4.1"
DRONE_PORT = 8888

# ESP32-CAM Specific Settings
ESP32_CAM_IP = "192.168.1.5"
ESP32_CAM_WEB_INTERFACE = "http://192.168.1.5"
ESP32_CAM_STREAM_URL = "http://192.168.1.5/sustain?stream=0"

# Testing and Calibration Settings
TEST_MODE = False              # Set to True for calibration mode
SHOW_DEBUG_INFO = True         # Show detailed detection info
SHOW_DETECTION_STATS = True    # Show detection statistics