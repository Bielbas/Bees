import os
import sys
import glob
import cv2
import numpy as np
import pandas as pd
from datetime import datetime
from pathlib import Path

from manual_cropper import ManualCropper
from image_processor import ImageProcessor
from bee_detector import BeeDetector


def main():
    """Main execution function."""
    print("🐝 Bee Detection and Area Calculation Project")
    print("=" * 50)
    
    input_dir = Path("input_photos")
    output_dir = Path("output")
    
    # Clean and create output directory
    if output_dir.exists():
        import shutil
        shutil.rmtree(output_dir)
        print("🧹 Cleaned output directory")
    output_dir.mkdir(exist_ok=True)
    
    if not input_dir.exists():
        print(f"❌ Input directory '{input_dir}' not found!")
        print("Please create the directory and add your hive photos.")
        return
    
    # Get all image files
    image_extensions = ['*.jpg', '*.jpeg', '*.png', '*.bmp', '*.tiff']
    image_files = []
    for ext in image_extensions:
        image_files.extend(glob.glob(str(input_dir / ext)))
        image_files.extend(glob.glob(str(input_dir / ext.upper())))
    
    if not image_files:
        print(f"❌ No image files found in '{input_dir}'!")
        print("Please add your hive photos to the input_photos directory.")
        return
    
    # Sort files by name
    image_files.sort()
    
    # Step 1: Manual cropping of the first image
    print("\n🖼️  Step 1: Manual cropping setup")
    first_image_path = image_files[0]
    print(f"Opening first image: {Path(first_image_path).name}")
    
    cropper = ManualCropper()
    crop_polygon = cropper.get_crop_polygon(first_image_path)
    if crop_polygon is None:
        print("❌ Cropping cancelled. Exiting...")
        return
    print(f"✅ Crop polygon saved: {crop_polygon}")
    
    # Step 2: Process all images
    print("\n🔄 Step 2: Processing all images")
    processor = ImageProcessor(crop_polygon)
    cropped_images = []
    
    for i, image_path in enumerate(image_files):
        print(f"Processing {i+1}/{len(image_files)}: {Path(image_path).name}")
        
        # Load and crop image
        cropped_img, crop_mask = processor.crop_image(image_path)
        if cropped_img is not None:
            cropped_images.append({
                'path': image_path,
                'image': cropped_img,
                'mask': crop_mask,
                'filename': Path(image_path).name
            })
            
            # Save cropped image
            output_path = output_dir / f"cropped_{Path(image_path).name}"
            cv2.imwrite(str(output_path), cropped_img)
    
    print(f"✅ Successfully processed {len(cropped_images)} images")
    
    # Step 3: Create background image
    print("\n🌅 Step 3: Creating background image")
    background_images = cropped_images[:min(15, len(cropped_images))]
    background = processor.create_background(background_images)
    
    if background is not None:
        bg_path = output_dir / "background.jpg"
        cv2.imwrite(str(bg_path), background)
        print(f"✅ Background image saved: {bg_path}")
    else:
        print("❌ Failed to create background image")
        return
    
    # Step 4: Detect bees and calculate areas with dynamic background updates
    print("\n🐝 Step 4: Detecting bees and calculating areas")
    detector = BeeDetector(background, processor.polygon_area)
    results = []
    
    BACKGROUND_UPDATE_INTERVAL = 50  # Update background every 50 photos
    
    for i, img_data in enumerate(cropped_images):
        # Update background every 50 images to adapt to lighting changes
        if i > 0 and i % BACKGROUND_UPDATE_INTERVAL == 0:
            print(f"\n🌅 Updating background after {i} images for lighting changes...")
            
            # Use next 15 images (or remaining) for new background
            start_idx = i
            end_idx = min(i + 15, len(cropped_images))
            background_subset = cropped_images[start_idx:end_idx]
            
            # Create new background
            new_background = processor.create_background(background_subset)
            if new_background is not None:
                detector.update_background(new_background)
                
                # Save the new background
                bg_path = output_dir / f"background_{i//BACKGROUND_UPDATE_INTERVAL + 1}.jpg"
                cv2.imwrite(str(bg_path), new_background)
                print(f"✅ New background saved: {bg_path}")
            else:
                print("⚠️ Failed to create new background, continuing with previous one")
        
        result = detector.analyze_image(img_data['image'], img_data['filename'])
        if result:
            results.append(result)
            
            # Save bee mask
            mask_path = output_dir / f"bee_mask_{img_data['filename']}"
            cv2.imwrite(str(mask_path), result['bee_mask'])
            
            # Save visualization
            vis = detector.create_visualization(img_data['image'], result['bee_mask'], [])
            vis_path = output_dir / f"visualization_{img_data['filename']}"
            cv2.imwrite(str(vis_path), vis)
            
            print(f"  {img_data['filename']}: {result['bee_percentage']:.2f}% bee coverage "
                  f"({result['num_bee_contours']} contours, {result['detection_method']})")
    
    # Step 5: Save results to CSV
    print("\n💾 Step 5: Saving results")
    if results:
        # Create simplified dataframe with only timestamp and percentage
        simplified_results = []
        for result in results:
            simplified_results.append({
                'timestamp': result['timestamp'],
                'bee_coverage_percent': result['bee_percentage']
            })
        
        df = pd.DataFrame(simplified_results)
        csv_path = "results.csv"
        df.to_csv(csv_path, index=False)
        print(f"✅ Results saved to: {csv_path}")
        
        # Print summary
        print(f"\n📊 Summary:")
        print(f"   Total images processed: {len(results)}")
        print(f"   Average bee coverage: {df['bee_coverage_percent'].mean():.2f}%")
        print(f"   Maximum bee coverage: {df['bee_coverage_percent'].max():.2f}%")
        print(f"   Minimum bee coverage: {df['bee_coverage_percent'].min():.2f}%")
    else:
        print("❌ No results to save")
    
    print("\n🎉 Processing complete!")


if __name__ == "__main__":
    main()
