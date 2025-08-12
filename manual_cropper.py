"""
Manual cropping tool for selecting hive inlet area.
"""

import cv2
import numpy as np


class ManualCropper:
    """Interactive tool for manually cropping the first image."""
    
    def __init__(self):
        self.points = []
        self.image = None
        self.clone = None
        self.done = False
    
    def mouse_callback(self, event, x, y, flags, param):
        """Handle mouse events for polygon selection."""
        if event == cv2.EVENT_LBUTTONDOWN and not self.done:
            self.points.append((x, y))
            temp_image = self.clone.copy()
            for i, pt in enumerate(self.points):
                cv2.circle(temp_image, pt, 3, (0, 255, 0), -1)
                if i > 0:
                    cv2.line(temp_image, self.points[i-1], pt, (0, 255, 0), 2)
            cv2.imshow("Crop Selection", temp_image)
        elif event == cv2.EVENT_RBUTTONDOWN and len(self.points) > 2:
            self.done = True
            temp_image = self.clone.copy()
            pts = np.array(self.points, np.int32)
            cv2.polylines(temp_image, [pts], isClosed=True, color=(0, 255, 0), thickness=2)
            cv2.imshow("Crop Selection", temp_image)
    
    def get_crop_polygon(self, image_path):
        """
        Open image and allow user to select polygon area.
        Returns:
            list: List of (x, y) points or None if cancelled
        """
        self.points = []
        self.done = False
        self.image = cv2.imread(image_path)
        if self.image is None:
            print(f"❌ Could not load image: {image_path}")
            return None
        height, width = self.image.shape[:2]
        max_display_size = 800
        if max(height, width) > max_display_size:
            scale = max_display_size / max(height, width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            display_image = cv2.resize(self.image, (new_width, new_height))
        else:
            display_image = self.image.copy()
            scale = 1.0
        self.image = display_image.copy()
        self.clone = display_image.copy()
        cv2.namedWindow("Crop Selection", cv2.WINDOW_AUTOSIZE)
        cv2.setMouseCallback("Crop Selection", self.mouse_callback)
        print("🖱️  Instructions:")
        print("   - Left click to add points (at least 3)")
        print("   - Right click to finish polygon")
        print("   - Press 'r' to reset selection")
        print("   - Press 'q' to quit")
        cv2.imshow("Crop Selection", self.image)
        while True:
            key = cv2.waitKey(1) & 0xFF
            if key == ord('r'):
                self.points = []
                self.done = False
                self.image = self.clone.copy()
                cv2.imshow("Crop Selection", self.image)
                print("🔄 Selection reset")
            elif key == ord('q'):
                cv2.destroyAllWindows()
                return None
            if self.done:
                cv2.destroyAllWindows()
                # Scale points back to original image size
                scaled_points = [(int(pt[0] / scale), int(pt[1] / scale)) for pt in self.points]
                return scaled_points
        cv2.destroyAllWindows()
        return None
