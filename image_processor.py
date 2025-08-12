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
        # Calculate the actual polygon area for accurate percentage calculations
        pts = np.array(crop_polygon, np.int32)
        self.polygon_area = cv2.contourArea(pts)
        print(f"✅ Polygon area calculated: {self.polygon_area} pixels")
    
    def crop_image(self, image_path):
        """
        Crop image using the stored polygon.
        Args:
            image_path: Path to the image file
        Returns:
            tuple: (cropped_image, polygon_mask) or (None, None) if failed
        """
        image = cv2.imread(image_path)
        if image is None:
            print(f"⚠️  Could not load image: {image_path}")
            return None, None
        return self.crop_image_array(image)

    def crop_image_array(self, image):
        """
        Crop image array using the stored polygon.
        Args:
            image: Image as numpy array
        Returns:
            tuple: (cropped_image, polygon_mask) - cropped image and mask of valid area
        """
        # Create polygon mask
        mask = np.zeros(image.shape[:2], dtype=np.uint8)
        pts = np.array(self.crop_polygon, np.int32)
        cv2.fillPoly(mask, [pts], 255)
        
        # Apply mask to image
        result = cv2.bitwise_and(image, image, mask=mask)
        
        # Crop to bounding box of polygon
        x, y, w, h = cv2.boundingRect(pts)
        cropped_image = result[y:y+h, x:x+w]
        cropped_mask = mask[y:y+h, x:x+w]
        
        return cropped_image, cropped_mask
    
    def create_background(self, image_list, method='median'):
        """
        Create background image from multiple images with improved robustness.
        
        Args:
            image_list: List of dictionaries with 'image' key containing numpy arrays
            method: Background creation method ('median', 'mean', 'mode')
            
        Returns:
            numpy.ndarray: Background image or None if failed
        """
        if not image_list:
            print("❌ No images provided for background creation")
            return None
        
        print(f"Creating background from {len(image_list)} images using {method} method...")
        
        # Stack all images
        images = [img_data['image'] for img_data in image_list]
        
        # Ensure all images have the same dimensions
        height, width = images[0].shape[:2]
        processed_images = []
        
        for img in images:
            if img.shape[:2] != (height, width):
                img = cv2.resize(img, (width, height))
            processed_images.append(img)
        
        # Stack images into a 4D array
        image_stack = np.stack(processed_images, axis=0)
        
        # Create background based on method
        if method == 'median':
            # Use median for robust background estimation
            background = np.median(image_stack, axis=0).astype(np.uint8)
        elif method == 'mean':
            background = np.mean(image_stack, axis=0).astype(np.uint8)
        elif method == 'mode':
            # Use median as approximation for mode (more stable)
            background = np.median(image_stack, axis=0).astype(np.uint8)
        else:
            print(f"❌ Unknown background method: {method}")
            return None
        
        # Apply slight blur to smooth the background
        background = cv2.GaussianBlur(background, (3, 3), 0)
        
        print(f"✅ Background created with dimensions: {background.shape}")
        return background
    
    def preprocess_image(self, image):
        """
        Preprocess image for better bee detection.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            numpy.ndarray: Preprocessed image
        """
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(image, (5, 5), 0)
        
        # Optional: enhance contrast
        lab = cv2.cvtColor(blurred, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        return enhanced
    
    # ...existing code...
    
    @staticmethod
    def calculate_image_area(image):
        """
        Calculate total image area in pixels.
        
        Args:
            image: Input image as numpy array
            
        Returns:
            int: Total area in pixels
        """
        return image.shape[0] * image.shape[1]
