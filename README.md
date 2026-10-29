# Snapchat Filter App Using Python 🎭

## 📌 Project Overview

This project is a **Snapchat-style Face Filter Application** developed using Python and OpenCV. It uses Haar Cascade Classifiers to detect faces through a webcam and applies visual filters to the detected faces in real time.

The project demonstrates how computer vision can be used to detect human faces and create interactive camera effects similar to those found in social media applications like Snapchat.

## ✨ Features

- **Real-Time Face Detection:** Detects faces using a webcam.
- **Haar Cascade Classifier:** Uses a pre-trained classifier for face detection.
- **Live Camera Feed:** Displays the webcam video in real time.
- **Face Filters:** Applies visual effects to detected faces.
- **Interactive Experience:** Allows users to see filter effects while moving in front of the camera.

*Note: The actual filters depend on the features implemented in your Python code.*

## 🛠️ Technologies Used

- **Python** – Main programming language.
- **OpenCV (`cv2`)** – Image processing and computer vision.
- **Haar Cascade Classifier** – Face detection.
- **Webcam** – Captures live video.

## 📂 Project Structure

```text
Snapchat-Filter-App/
│
├── snapchat_filter.py
├── haarcascade_frontalface_default.xml
├── requirements.txt
└── README.md
```

*Your Python filename and XML filename may differ. Update the names above to match your actual files.*

## ⚙️ Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/YOUR-USERNAME/Snapchat-Filter-App.git
```

### 2. Open the Project Folder

```bash
cd Snapchat-Filter-App
```

### 3. Install the Required Library

```bash
pip install opencv-python
```

### 4. Run the Application

```bash
python snapchat_filter.py
```

Make sure your webcam is connected and the Haar Cascade XML file is available at the path specified in your Python code.

## 🧠 How It Works

1. The application opens the webcam using OpenCV.
2. Each video frame is captured and processed.
3. The frame is converted into grayscale for face detection.
4. The Haar Cascade Classifier identifies possible faces.
5. The application uses the detected face coordinates to position the filter.
6. The modified frames are displayed continuously until the user exits the application.

## 📚 What I Learned

- Basics of computer vision using Python.
- Working with OpenCV and webcam video streams.
- Understanding Haar Cascade face detection.
- Processing images frame by frame.
- Using face coordinates to apply visual effects.
- Building an interactive real-time camera application.

## 🚀 Future Improvements

- Add more filters, such as sunglasses, animal ears, and masks.
- Add a graphical user interface using CustomTkinter.
- Include buttons to switch between filters.
- Capture and save filtered photos.
- Explore advanced face landmark detection using MediaPipe.

## 🎯 Applications

- Face filter applications.
- Interactive camera effects.
- Computer vision learning projects.
- Social media-style photo applications.
- Prototype development for augmented reality experiences.

## 👩‍💻 Author

**Tejaswini Bhosale**

Python | OpenCV | Computer Vision

## 📄 License

This project is available for educational and learning purposes. You may add an MIT License if you want to allow others to reuse and modify the code under its terms.
