# Bachelor's Thesis Project

**Topic:** Analysis of bee apiary data using machine learning methods 
**Degree:** Bachelor of Engineering  

---

## Overview

This project is developed as a Bachelor's thesis and proposes a low-cost, telephone-based hardware unit for continuous monitoring of bee activity in a hive. A companion mobile application receives image frames, runs an on-device/edge ML model to detect bees, and generates real-time charts showing the percentage of the hive inlet occupied by bees.

---

## Objectives

- Design and build a repurposed hardware telephone unit with a camera to capture live images of a beehive entrance.  
- Develop a cross-platform mobile application to:  
  1. Stream images from the hardware device.  
  2. Run a lightweight convolutional neural network (CNN) to detect and count bees per frame.  
  3. Compute the fraction of the image area covered by bees.  
  4. Display time-series charts and statistics.  
- Evaluate detection accuracy and system performance under varying light/weather conditions.

---

## System Architecture

### Hardware
- **Base Unit:** Modified analog/digital telephone chassis  
- **Camera Module:** 5 MP fisheye lens for wide-angle hive entrance coverage  
- **Compute:** Single-board computer (e.g., Raspberry Pi or equivalent)  
- **Connectivity:** Wi-Fi / 4G LTE modem (depending on remote site)  
- **Power:** PoE adapter or solar-rechargeable battery  

### Mobile App
- **Technology:** React Native or Flutter for Android/iOS  
- **Features:**  
  - Live video stream viewer  
  - On-device ML inference (TensorFlow Lite / Core ML)  
  - Dashboard with historical charts  
  - Alerts for unusual activity patterns  

### Machine Learning Model
- **Architecture:** Custom lightweight CNN based on MobileNetV2  
- **Training Data:**  
  - Manually annotated hive entrance images  
  - Data augmentation (brightness, rotation, scale)  
- **Metrics:** Precision/recall on bee detection; frame-rate inference speed  

