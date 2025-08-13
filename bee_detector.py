import cv2
import numpy as np
from datetime import datetime


DETECTION_THRESHOLDS = [15, 25, 35, 45]
MIN_BEE_AREA = 20
MAX_BEE_AREA = 8000
COLOR_LOWER_BEE = [5, 20, 20]
COLOR_UPPER_BEE = [25, 255, 180]
MIN_ASPECT_RATIO = 0.3
MAX_ASPECT_RATIO = 3.0
MIN_SOLIDITY = 0.3


class BeeDetector:
    """Detects bees using background subtraction and calculates occupied area."""
    
    def __init__(self, background_image, valid_area_pixels=None):
        """
        Initialize detector with background image.
        
        Args:
            background_image: Background image as numpy array
            valid_area_pixels: Actual valid area in pixels (for polygon cropping)
        """
        self.background = background_image
        self.background_gray = cv2.cvtColor(background_image, cv2.COLOR_BGR2GRAY)
        self.valid_area_pixels = valid_area_pixels
        
        self.thresholds = DETECTION_THRESHOLDS
        self.min_area = MIN_BEE_AREA
        self.max_area = MAX_BEE_AREA
        self.color_lower_bee = np.array(COLOR_LOWER_BEE)
        self.color_upper_bee = np.array(COLOR_UPPER_BEE)
        self.min_aspect_ratio = MIN_ASPECT_RATIO
        self.max_aspect_ratio = MAX_ASPECT_RATIO
        self.min_solidity = MIN_SOLIDITY
    
    def detect_bees(self, image, threshold=None, min_area=None, max_area=None):
        """
        Detect bees using improved background subtraction and morphological operations.
        
        Args:
            image: Input image as numpy array
            threshold: Difference threshold for background subtraction (uses default if None)
            min_area: Minimum contour area (uses default if None)
            max_area: Maximum contour area (uses default if None)
            
        Returns:
            tuple: (bee_mask, bee_contours)
        """
        if threshold is None:
            threshold = 25
        if min_area is None:
            min_area = self.min_area
        if max_area is None:
            max_area = self.max_area
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        gray_blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        background_blurred = cv2.GaussianBlur(self.background_gray, (3, 3), 0)
        
        # Background subtraction
        diff = cv2.absdiff(background_blurred, gray_blurred)
        
        # Apply adaptive threshold for better detection
        _, thresh = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)
        
        # Alternative: use Otsu's thresholding for automatic threshold selection
        _, thresh_otsu = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # Combine both thresholds (take maximum)
        thresh = cv2.bitwise_or(thresh, thresh_otsu)
        
        # Morphological operations to clean up the mask
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
        
        # Remove small noise
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # Fill small holes
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel_close, iterations=1)
        
        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Filter contours by area and shape
        bee_contours = []
        bee_mask = np.zeros_like(thresh)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if min_area <= area <= max_area:
                # Additional shape filtering: check aspect ratio and solidity
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = float(w) / h
                hull = cv2.convexHull(contour)
                hull_area = cv2.contourArea(hull)
                solidity = area / hull_area if hull_area > 0 else 0
                
                # Bees are roughly circular/oval, so filter extreme aspect ratios
                if (self.min_aspect_ratio <= aspect_ratio <= self.max_aspect_ratio and 
                    solidity > self.min_solidity):
                    bee_contours.append(contour)
                    cv2.fillPoly(bee_mask, [contour], 255)
        
        return bee_mask, bee_contours
    
    def update_background(self, new_background_image):
        """
        Update the background image for changing lighting conditions.
        
        Args:
            new_background_image: New background image as numpy array
        """
        self.background = new_background_image
        self.background_gray = cv2.cvtColor(new_background_image, cv2.COLOR_BGR2GRAY)
    
    def calculate_bee_area(self, bee_mask):
        """
        Calculate the total area occupied by bees.
        
        Args:
            bee_mask: Binary mask of bee locations
            
        Returns:
            int: Total bee area in pixels
        """
        return np.sum(bee_mask > 0)
    
    def calculate_total_area(self, image):
        """
        Calculate total valid image area (excluding black background from polygon cropping).
        
        Args:
            image: Input image
            
        Returns:
            int: Total valid area in pixels
        """
        if self.valid_area_pixels:
            return self.valid_area_pixels
        else:
            return image.shape[0] * image.shape[1]
    
    def analyze_image(self, image, filename, adaptive_threshold=True):
        """
        Complete analysis of an image for bee detection with multiple methods.
        
        Args:
            image: Input image as numpy array
            filename: Name of the image file
            adaptive_threshold: Whether to use adaptive thresholding
            
        Returns:
            dict: Analysis results
        """
        best_result = None
        best_score = -1
        
        # Method 1: Standard background subtraction with multiple thresholds
        for threshold in self.thresholds:
            bee_mask, contours = self.detect_bees(image, threshold=threshold)
            
            # Calculate metrics
            bee_area = self.calculate_bee_area(bee_mask)
            total_area = self.calculate_total_area(image)
            bee_percentage = (bee_area / total_area) * 100
            
            # Score based on number of reasonable-sized contours and coverage
            num_contours = len(contours)
            coverage_score = min(bee_percentage, 60)  # Cap at 60% to avoid noise
            contour_score = min(num_contours * 2, 20)  # Reward having multiple bees
            score = coverage_score + contour_score
            
            if score > best_score:
                best_score = score
                best_result = {
                    'filename': filename,
                    'timestamp': datetime.now().isoformat(),
                    'bee_area_pixels': int(bee_area),
                    'total_area_pixels': int(total_area),
                    'bee_percentage': round(bee_percentage, 3),
                    'num_bee_contours': len(contours),
                    'threshold_used': threshold,
                    'detection_method': 'background_subtraction',
                    'score': round(score, 2),
                    'bee_mask': bee_mask
                }
        
        # Method 2: Alternative color-based detection for high bee density
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # Use class color thresholds
        color_mask = cv2.inRange(hsv, self.color_lower_bee, self.color_upper_bee)
        
        # Clean up color mask
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        color_mask = cv2.morphologyEx(color_mask, cv2.MORPH_OPEN, kernel)
        color_mask = cv2.morphologyEx(color_mask, cv2.MORPH_CLOSE, kernel)
        
        # Calculate color-based metrics
        color_bee_area = np.sum(color_mask > 0)
        color_bee_percentage = (color_bee_area / self.calculate_total_area(image)) * 100
        
        # If color detection shows significantly higher bee coverage, use it
        # More liberal conditions for color segmentation
        if color_bee_percentage > best_result['bee_percentage'] * 1.2 and color_bee_percentage > 3:
            contours_color, _ = cv2.findContours(color_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            # Use the same filters as in config.py
            filtered_contours = [c for c in contours_color if self.min_area <= cv2.contourArea(c) <= self.max_area]
            
            best_result.update({
                'bee_area_pixels': int(color_bee_area),
                'bee_percentage': round(color_bee_percentage, 3),
                'num_bee_contours': len(filtered_contours),
                'threshold_used': 'color_based',
                'detection_method': 'color_segmentation',
                'bee_mask': color_mask
            })
        
        return best_result
    
    def create_visualization(self, image, bee_mask, contours):
        """
        Create visualization of bee detection results.
        
        Args:
            image: Original image
            bee_mask: Binary mask of detected bees
            contours: List of bee contours
            
        Returns:
            numpy.ndarray: Visualization image
        """
        # Create visualization
        vis = image.copy()
        
        # Overlay bee mask in red
        red_overlay = np.zeros_like(image)
        red_overlay[:, :, 2] = bee_mask  # Red channel
        vis = cv2.addWeighted(vis, 0.7, red_overlay, 0.3, 0)
        
        # Draw contour boundaries
        cv2.drawContours(vis, contours, -1, (0, 255, 0), 2)
        
        return vis
