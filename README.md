# ESP32-CAM Human Motion Detection

A Python-based motion detection system optimized for detecting human movement using ESP32-CAM live video streams.

## Features

- **Human-Optimized Detection**: Specifically tuned to detect human movement
- **Smart Image Saving**: Saves detected motion frames WITH detection boxes drawn
- **Adaptive Thresholding**: Automatically adjusts sensitivity based on lighting
- **Contour Merging**: Combines nearby detections for better human recognition
- **Real-time Analysis**: Live motion detection with visual feedback
- **Detailed Logging**: Comprehensive motion event logging

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Camera**:
   - Update `config.py` with your ESP32-CAM stream URL
   - Default: `http://192.168.1.5/sustain?stream=0`

3. **Run Motion Detection**:
   ```bash
   python motion_detector.py
   ```

## Controls

- **'q'** - Quit detection
- **'s'** - Save current frame manually  
- **'r'** - Reset background manually
- **'t'** - Toggle threshold analysis view

## Configuration

Key settings in `config.py`:

```python
# Detection sensitivity
MOTION_THRESHOLD = 35          # Lower = more sensitive
MIN_CONTOUR_AREA = 800         # Minimum motion size
MIN_HUMAN_AREA = 3000          # Minimum size for human classification

# Processing
GAUSSIAN_BLUR_SIZE = 21        # Noise reduction
MOTION_PERSISTENCE_FRAMES = 2   # Frames required for detection
```

## File Structure

```
├── config.py              # Main configuration
├── motion_detector.py      # Motion detection engine
├── motion_frames/          # Saved detection images (auto-created)
├── motion_log.txt         # Detection event log
└── requirements.txt       # Python dependencies
```

## Detection Types

- **Green Boxes**: Regular motion detection
- **Cyan Boxes**: Human-sized detection (large areas)
- **Saved Images**: Include detection boxes and information overlay

## Troubleshooting

### Too Sensitive (False Positives)
```python
MOTION_THRESHOLD = 45          # Increase threshold
MIN_CONTOUR_AREA = 1200        # Ignore smaller movements
```

### Not Sensitive Enough (Missing Humans)
```python
MOTION_THRESHOLD = 25          # Decrease threshold  
MIN_CONTOUR_AREA = 500         # Detect smaller movements
```

### Poor Detection in Dark/Bright Conditions
- Enable `ADAPTIVE_THRESHOLD = True` (default)
- Press 'r' to reset background when lighting changes

## ESP32-CAM Setup

1. Flash MJPEG2SD firmware to ESP32-CAM
2. Connect to your WiFi network
3. Access web interface at device IP
4. Click "Start Stream" 
5. Use stream URL in config.py

## Hardware Requirements

- ESP32-CAM module with MJPEG2SD firmware
- Stable WiFi connection
- Python 3.7+ with OpenCV

## License

MIT License - see LICENSE file for details.