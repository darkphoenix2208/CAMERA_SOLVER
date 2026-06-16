# Puzzle Vision 🧩🎲

![React](https://img.shields.io/badge/react-%2320232a.svg?style=for-the-badge&logo=react&logoColor=%2361DAFB)
![FastAPI](https://img.shields.io/badge/FastAPI-005571?style=for-the-badge&logo=fastapi)
![OpenCV](https://img.shields.io/badge/opencv-%23white.svg?style=for-the-badge&logo=opencv&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)

An AI-powered Augmented Reality solver suite for physical puzzles like Sudoku and Rubik's Cubes, built as a full-stack progressive web application.

## Why this project?

I built **Puzzle Vision** to showcase my ability to seamlessly integrate modern web technologies (React/Vite) with complex backend algorithms and computer vision pipelines (FastAPI/OpenCV). This project solves a real-world problem—bridging the gap between physical objects and digital algorithms—and demonstrates my proficiency in system design, machine learning, and full-stack development.

## Features

- 📸 **AR Camera Integration:** Real-time continuous scanning from any mobile or desktop webcam.
- 🧩 **Sudoku AR Overlay:** Uses contour detection, a custom Neural Network (MLP), and backtracking to instantly solve and project missing digits right back onto the physical board.
- 🎲 **Rubik's Cube 3D Solver:** Scans face colors under varying lighting conditions with HSV calibration, generates a Kociemba algorithm solution, and animates it on a 3D Canvas using Three.js.
- ⚡ **Benchmarking & Confidence Scoring:** Real-time metrics showing solve times (often <20ms) and OCR confidence percentages.
- 📱 **Progressive Web App (PWA):** Fully responsive mobile-first UI with offline capabilities.

## Tech Stack

**Frontend:**
- React 18 & Vite
- @react-three/fiber & @react-three/drei for 3D rendering
- react-webcam for video capture

**Backend:**
- FastAPI & Uvicorn
- OpenCV & NumPy for image processing
- scikit-learn for custom digit recognition ML model
- Kociemba for optimal Rubik's Cube solving

**DevOps & Testing:**
- Pytest & HTTPX for integration testing
- GitHub Actions for CI/CD
- Dockerized backend

## Setup Guide

### 1. Backend (Python/FastAPI)

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
python main.py
```
*Note: Ensure Tesseract OCR and libgl1-mesa-glx are installed on your system if running outside Docker.*

### 2. Frontend (React/Vite)

```bash
cd frontend
npm install
npm run dev
```

The React app will proxy API requests to `http://localhost:8000`. Open `http://localhost:5173` to view the app!
