import cv2
import numpy as np
from pathlib import Path


class ImageProcessor:
    """Handles image cropping and background generation."""
    
    def __init__(self, crop_polygon):
        """
        Initialize with crop polygon coordinates.
        Args:
            crop_polygon: List of (x, y) points
        """
        self.crop_polygon = crop_polygon
        pts = np.array(crop_polygon, np.int32)
        self.polygon_area = cv2.contourArea(pts)
    
    
    def crop_image_array(self, image):
        """Crop image array using the stored polygon"""

        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        pts = np.array(self.crop_polygon, np.int32)
        cv2.fillPoly(mask, [pts], 255)
        
        result = cv2.bitwise_and(image, image, mask=mask)
        
        x, y, w, h = cv2.boundingRect(pts)
        cropped_image = result[y:y+h, x:x+w]
        cropped_mask = mask[y:y+h, x:x+w]
        
        return cropped_image, cropped_mask
    

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
        background = cv2.GaussianBlur(background, (3, 3), 0)
        
        return background

