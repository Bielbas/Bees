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

---

## Installation & Setup

1. **Hardware Assembly**  
   - Install camera in telephone housing.  
   - Flash the compute module with `raspbian-lite` or your preferred Linux distro.  
   - Configure Wi-Fi/4G credentials in `/etc/network/interfaces`.  

2. **Mobile App Setup**  
   ```bash
   git clone https://github.com/your-org/BeeWatch-App.git
   cd BeeWatch-App
   npm install      # or yarn install
   ```

3. **Deploying ML Model**  
   - Place the `.tflite` model file into `assets/models/`.  
   - Update model path in `src/config.ts`.  

4. **Running**  
   - **Hardware Unit:**  
     ```bash
     python3 stream_server.py --port 8000
     ```  
   - **Mobile App (Dev Mode):**  
     ```bash
     npm run start
     ```

---

## Usage

1. Power on the hardware telephone and ensure network connectivity.  
2. Launch the BeeWatch app on your phone.  
3. Connect to the device's streaming endpoint (e.g., `http://192.168.1.100:8000`).  
4. View live video—bee detections and occupancy percentage will update in real time.  
5. Navigate to the "History" tab to see charts of bee coverage over the past hours/days.

---

## Data Collection & Visualization

- **Raw Frames:** Stored (optional) on SD card for offline labeling.  
- **Inference Logs:** JSON entries with timestamp, bee count, occupancy ratio.  
- **Charts:**  
  - _Occupancy % over time_  
  - _Bee count per minute_  

Data files are saved under `/data/logs/`. Use built-in export to CSV for further analysis.

---

## Contributing

We welcome improvements! To contribute:

1. Fork the repository.  
2. Create a feature branch (`git checkout -b feature/awesome`).  
3. Commit your changes (`git commit -m "Add awesome feature"`).  
4. Push to your branch (`git push origin feature/awesome`).  
5. Open a Pull Request.

Please follow the [Code of Conduct](./CODE_OF_CONDUCT.md) and [Contribution Guidelines](./CONTRIBUTING.md).

---

## License

This project is licensed under the MIT License. See [LICENSE](./LICENSE) for details.

---

## Contact

**Supervisor:** Prof. Jane Smith  
**Email:** jane.smith@university.edu  
**Author:** [Your Name] – your.email@domain.edu  
**Repository:** https://github.com/your-org/BeeWatch  

---

*This project fulfills the requirements of the Bachelor's degree in [Your Department], [Your University].*
