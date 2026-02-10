import cv2
import numpy as np
from datetime import datetime


DETECTION_THRESHOLDS = [8, 18, 28, 38]
MIN_BEE_AREA = 50
MAX_BEE_AREA = 2500
COLOR_LOWER_BEE = [5, 18, 18]
COLOR_UPPER_BEE = [25, 255, 190]
MIN_ASPECT_RATIO = 0.3
MAX_ASPECT_RATIO = 3.0
MIN_SOLIDITY = 0.25


class BeeDetector:
    """Detects bees using background subtraction and calculates occupied area"""
    
    def __init__(self, background_image, valid_area_pixels=None):
        """Initialize detector with background image."""
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
        """Detect bees using improved background subtraction and morphological operations."""
        if threshold is None:
            threshold = 25
        if min_area is None:
            min_area = self.min_area
        if max_area is None:
            max_area = self.max_area
        
        # Ensure image matches background size
        if image.shape[:2] != self.background.shape[:2]:
            image = cv2.resize(image, (self.background.shape[1], self.background.shape[0]))
        
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        gray_blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        background_blurred = cv2.GaussianBlur(self.background_gray, (3, 3), 0)
        
        diff = cv2.absdiff(background_blurred, gray_blurred)

        _, thresh = cv2.threshold(diff, threshold, 255, cv2.THRESH_BINARY)
        _, thresh_otsu = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        thresh = cv2.bitwise_or(thresh, thresh_otsu)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
        
        kernel_close = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel_close, iterations=1)
        
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        bee_contours = []
        bee_mask = np.zeros_like(thresh)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if min_area <= area <= max_area:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = float(w) / h
                hull = cv2.convexHull(contour)
                hull_area = cv2.contourArea(hull)
                solidity = area / hull_area if hull_area > 0 else 0
                
                if (self.min_aspect_ratio <= aspect_ratio <= self.max_aspect_ratio and 
                    solidity > self.min_solidity):
                    bee_contours.append(contour)
                    cv2.fillPoly(bee_mask, [contour], 255)
        
        return bee_mask, bee_contours
    
    def update_background(self, new_background_image):
        """Update the background image for changing lighting conditions"""

        self.background = new_background_image
        self.background_gray = cv2.cvtColor(new_background_image, cv2.COLOR_BGR2GRAY)
    
    def calculate_bee_area(self, bee_mask):
        """Calculate the total area occupied by bees"""

        return np.sum(bee_mask > 0)
    
    def calculate_total_area(self, image):
        """Calculate total valid image area excluding black background"""

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
        
        for threshold in self.thresholds:
            bee_mask, contours = self.detect_bees(image, threshold=threshold)
            
            bee_area = self.calculate_bee_area(bee_mask)
            total_area = self.calculate_total_area(image)
            bee_percentage = (bee_area / total_area) * 100
            
            num_contours = len(contours)
            coverage_score = min(bee_percentage, 60)  
            contour_score = min(num_contours * 2, 20)  
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
        
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        color_mask = cv2.inRange(hsv, self.color_lower_bee, self.color_upper_bee)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (2, 2))
        color_mask = cv2.morphologyEx(color_mask, cv2.MORPH_OPEN, kernel)
        color_mask = cv2.morphologyEx(color_mask, cv2.MORPH_CLOSE, kernel)
        
        color_bee_area = np.sum(color_mask > 0)
        color_bee_percentage = (color_bee_area / self.calculate_total_area(image)) * 100
        

        if color_bee_percentage > best_result['bee_percentage'] * 1.2 and color_bee_percentage > 3:
            contours_color, _ = cv2.findContours(color_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
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
        """Create visualization of bee detection results"""

        vis = image.copy()
        red_overlay = np.zeros_like(image)
        red_overlay[:, :, 2] = bee_mask
        vis = cv2.addWeighted(vis, 0.7, red_overlay, 0.3, 0)
        cv2.drawContours(vis, contours, -1, (0, 255, 0), 2)
        
        return vis
