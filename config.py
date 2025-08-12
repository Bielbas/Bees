"""
Configuration file for bee detection parameters.
Adjust these values to fine-tune detection accuracy.
"""

# Detection thresholds for background subtraction
# Lower values = more sensitive (detects smaller differences)
# Higher values = less sensitive (only detects larger differences)
DETECTION_THRESHOLDS = [10, 15, 20, 25, 30]  # Dodane niższe progi dla lepszej detekcji

# Size filters for bee contours (in pixels)
MIN_BEE_AREA = 8       # Zmniejszone - będzie wykrywać mniejsze pszczoły
MAX_BEE_AREA = 12000   # Zwiększone - będzie wykrywać większe pszczoły/grupy

# Color detection for bees in HSV color space
# Hue: 5-25 (brown/orange colors)
# Saturation: 20-255 (avoid very gray colors)  
# Value: 20-180 (avoid very bright/dark areas)
COLOR_LOWER_BEE = [5, 20, 20]
COLOR_UPPER_BEE = [25, 255, 180]

# Shape filtering parameters
MIN_ASPECT_RATIO = 0.2   # Bardziej liberalne - pszczoły mogą być różnie ułożone
MAX_ASPECT_RATIO = 5.0   # Bardziej liberalne - pszczoły mogą być wydłużone
MIN_SOLIDITY = 0.2       # Bardziej liberalne - akceptuje mniej regularne kształty

# Background creation
BACKGROUND_METHOD = 'median'  # 'median', 'mean', or 'mode'
MAX_BACKGROUND_IMAGES = 8     # Number of images to use for background (zmniejszone dla łatwiejszego testowania)

# Output settings
SAVE_DEBUG_IMAGES = True      # Save visualization and mask images
VERBOSE_DEBUG = True          # Print detailed debug information

# Tips for adjustment:
# - If missing bees: Lower DETECTION_THRESHOLDS, increase MAX_BEE_AREA
# - If too many false positives: Raise DETECTION_THRESHOLDS, decrease MAX_BEE_AREA
# - If bees are wrong color: Adjust COLOR_LOWER_BEE and COLOR_UPPER_BEE
# - If irregular shapes detected: Increase MIN_SOLIDITY
