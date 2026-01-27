import cv2
import numpy as np
from pathlib import Path


class ImageProcessor:
    """Handles image cropping and background generation."""
    
    def __init__(self, crop_polygon):
        """
        Initialize with crop polygon coordinates.
        Args:
            crop_polygon: List of (x, y) points or None to disable cropping
        """
        self.crop_polygon = crop_polygon
        if crop_polygon is not None:
            pts = np.array(crop_polygon, np.int32)
            self.polygon_area = cv2.contourArea(pts)
        else:
            self.polygon_area = None
    
    
    def crop_image_array(self, image):
        """Crop image array using the stored polygon (or return original if no polygon)"""
        
        # If no polygon, return the image as-is
        if self.crop_polygon is None:
            return image, None

        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        pts = np.array(self.crop_polygon, np.int32)
        cv2.fillPoly(mask, [pts], 255)
        
        result = cv2.bitwise_and(image, image, mask=mask)
        

        return result, mask
    

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

