#!/usr/bin/env python3
"""
Configuration file for motion detection
Adjust these parameters to fine-tune motion detection
"""

# Camera Settings
CAMERA_INDEX = 0  # Change this based on your camera test results
CAMERA_WIDTH = 640
CAMERA_HEIGHT = 480
FPS = 30

# Motion Detection Settings
MOTION_THRESHOLD = 25  # Minimum change between frames to detect motion (0-255)
MIN_CONTOUR_AREA = 500  # Minimum area of motion to be considered significant
MAX_CONTOUR_AREA = 50000  # Maximum area to filter out camera shake

# Frame Processing
GAUSSIAN_BLUR_SIZE = 21  # Size of blur kernel (must be odd number)
MORPHOLOGY_KERNEL_SIZE = 5  # Size of morphological operations kernel

# Alert Settings
MOTION_ALERT_COOLDOWN = 2.0  # Seconds between motion alerts
SAVE_MOTION_FRAMES = True  # Save frames when motion is detected
MOTION_FRAMES_DIR = "motion_frames"  # Directory to save motion frames

# Display Settings
SHOW_THRESHOLD_IMAGE = False  # Show the threshold/difference image
SHOW_CONTOURS = True  # Draw bounding boxes around detected motion
WINDOW_SCALE = 1.0  # Scale factor for display window

# Colors (BGR format)
MOTION_BOX_COLOR = (0, 255, 0)  # Green
ALERT_TEXT_COLOR = (0, 0, 255)  # Red
INFO_TEXT_COLOR = (255, 255, 255)  # White

# Logging
LOG_MOTION_EVENTS = True
LOG_FILE = "motion_log.txt"

# Advanced Settings
BACKGROUND_SUBTRACTION_HISTORY = 500  # Frames for background model
BACKGROUND_SUBTRACTION_THRESHOLD = 50
MOTION_DETECTION_METHOD = "frame_diff"  # Options: "frame_diff", "background_sub"

# Future Integration Settings (for drone communication)
DRONE_COMMUNICATION = False
DRONE_IP = "192.168.4.1"
DRONE_PORT = 8888