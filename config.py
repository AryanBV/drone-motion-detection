#!/usr/bin/env python3
"""
Optimized Configuration for ESP32-CAM Human Motion Detection
Tuned specifically for detecting human movement with proper image saving
"""

# Camera Settings - ESP32-CAM Stream  
CAMERA_INDEX = "http://192.168.195.193/stream"
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
FPS = 30

# Motion Detection Settings - OPTIMIZED FOR HUMAN DETECTION
MOTION_THRESHOLD = 35          # Optimized for human movement (was 50)
MIN_CONTOUR_AREA = 800         # Lowered to detect human body parts (was 2500)
MAX_CONTOUR_AREA = 50000       # Keep large movements

# Frame Processing - HUMAN-OPTIMIZED
GAUSSIAN_BLUR_SIZE = 21        # Reduced to preserve human details (was 31)
MORPHOLOGY_KERNEL_SIZE = 5     # Reduced to keep human features (was 9)

# Motion Persistence Settings - RELAXED FOR HUMANS
MOTION_PERSISTENCE_FRAMES = 2   # Reduced for variable human movement (was 3)
BACKGROUND_UPDATE_RATE = 0.005  # Slower background adaptation (was 0.01)

# Human Detection Enhancement
MERGE_NEARBY_CONTOURS = True    # Merge close contours for better human detection
CONTOUR_MERGE_DISTANCE = 100    # Distance threshold for merging contours
MIN_HUMAN_AREA = 3000          # Minimum area considered as full human
MAX_DETECTION_OBJECTS = 5       # Limit objects per frame to reduce noise

# Alert Settings
MOTION_ALERT_COOLDOWN = 3.0    # Time between alerts
SAVE_MOTION_FRAMES = True      # Save detected motion frames
MOTION_FRAMES_DIR = "motion_frames"

# Display Settings
SHOW_THRESHOLD_IMAGE = True    # Shows detection processing
SHOW_CONTOURS = True           # Draw detection boxes
WINDOW_SCALE = 1.0             # Display scale factor

# Colors (BGR format)
MOTION_BOX_COLOR = (0, 255, 0)     # Green boxes around motion
ALERT_TEXT_COLOR = (0, 0, 255)     # Red text for alerts
INFO_TEXT_COLOR = (255, 255, 255)  # White text for info
DETECTION_STATS_COLOR = (0, 255, 255)  # Yellow for detection stats
HUMAN_BOX_COLOR = (0, 255, 255)    # Cyan for large human detections

# Logging
LOG_MOTION_EVENTS = True
LOG_FILE = "motion_log.txt"

# Advanced Settings
BACKGROUND_SUBTRACTION_HISTORY = 500
BACKGROUND_SUBTRACTION_THRESHOLD = 50
MOTION_DETECTION_METHOD = "frame_diff"

# Sensitivity Control
AUTO_RESET_BACKGROUND = True    # Automatically reset background
RESET_BACKGROUND_INTERVAL = 300 # Reset every 5 minutes
ADAPTIVE_THRESHOLD = True       # Adjust threshold based on lighting

# Image Saving Enhancement
SAVE_WITH_DETECTION_BOXES = True   # Save images with detection visualization
ADD_TIMESTAMP_TO_SAVED_IMAGES = True
SAVE_DETECTION_INFO_ON_IMAGE = True

# Future Integration Settings (for drone communication)
DRONE_COMMUNICATION = False
DRONE_IP = "192.168.4.1"
DRONE_PORT = 8888

# ESP32-CAM Specific Settings
ESP32_CAM_IP = "192.168.195.193"
ESP32_CAM_WEB_INTERFACE = "http://192.168.195.193"
ESP32_CAM_STREAM_URL = "http://192.168.195.193/sustain?stream=0"

# Testing and Calibration
TEST_MODE = False
SHOW_DEBUG_INFO = True
SHOW_DETECTION_STATS = True