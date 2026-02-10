import cv2
import numpy as np
from pathlib import Path


class ImageProcessor:
    """Handles image cropping and background generation."""
    
    def __init__(self, crop_polygon=None):
        """
        Initialize with crop polygon coordinates.
        Args:
            crop_polygon: List of (x, y) points or None to disable cropping (images pre-processed)
        """
        self.crop_polygon = crop_polygon
        self.polygon_area = None
    
    
    def crop_image_array(self, image):
        """Return image as-is (images are pre-processed with polygon mask)"""
        return image, None
    
    def calculate_valid_area(self, image):
        """Calculate valid (non-black) area in preprocessed image"""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        _, mask = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)
        return np.sum(mask > 0)
    

    def create_background(self, image_list):
        """
        Create background image from multiple images with improved robustness.
        
        Args:
            image_list: List of dictionaries with 'image' key containing numpy arrays
            
        Returns:
            numpy.ndarray: Background image or None if failed
        """
        
        if not image_list:
            print("No images provided for background creation")
            return None
                
        images = [img_data['image'] for img_data in image_list]
        height, width = images[0].shape[:2]
        processed_images = []
        for img in images:
            if img.shape[:2] != (height, width):
                img = cv2.resize(img, (width, height))
            processed_images.append(img)
        
        image_stack = np.stack(processed_images, axis=0)
        background = np.median(image_stack, axis=0).astype(np.uint8)
        
        background = cv2.bilateralFilter(background, 15, 80, 80)
        background = cv2.GaussianBlur(background, (5, 5), 0)
        
        return background

