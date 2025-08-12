"""
Setup script to get crop polygon for API.
"""

import pickle
from pathlib import Path
from manual_cropper import ManualCropper

def setup_crop_polygon():
    """Setup crop polygon from first image."""
    input_dir = Path("input_photos")
    
    if not input_dir.exists() or not list(input_dir.glob("*.jpg")):
        print("❌ Brak zdjęć w folderze input_photos/")
        print("Dodaj przynajmniej jedno zdjęcie do testowania")
        return None
    
    # Get first image
    image_files = list(input_dir.glob("*.jpg")) + list(input_dir.glob("*.jpeg")) + list(input_dir.glob("*.png"))
    first_image = str(image_files[0])
    
    print(f"🖼️ Używam {first_image} do definiowania obszaru")
    
    # Get crop polygon
    cropper = ManualCropper()
    crop_polygon = cropper.get_crop_polygon(first_image)
    
    if crop_polygon:
        # Save to file
        with open("crop_polygon.pkl", "wb") as f:
            pickle.dump(crop_polygon, f)
        
        print(f"✅ Polygon zapisany: {crop_polygon}")
        print("💾 Zapisano do crop_polygon.pkl")
        return crop_polygon
    else:
        print("❌ Nie udało się zdefiniować polygon")
        return None

if __name__ == "__main__":
    setup_crop_polygon()
