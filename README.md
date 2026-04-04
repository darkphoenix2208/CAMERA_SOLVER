<div align="center">
  <img src="https://img.icons8.com/color/120/000000/rubiks-cube.png" alt="Rubik's Cube" width="80" />
  <img src="https://img.icons8.com/color/120/000000/sudoku.png" alt="Sudoku" width="80" />

  <h1>Camera Solver</h1>
  
  <p>
    An intelligent, full-stack <strong>Computer Vision application</strong> that automatically extracts and solves visual puzzles like Sudoku boards and Rubik's Cubes straight from your camera.
  </p>

  <div>
    <img src="https://img.shields.io/badge/Frontend-React%20%2B%20Vite-blue?style=for-the-badge&logo=react" alt="Frontend" />
    <img src="https://img.shields.io/badge/Backend-FastAPI-009688?style=for-the-badge&logo=fastapi" alt="Backend" />
    <img src="https://img.shields.io/badge/Vision-OpenCV-green?style=for-the-badge&logo=opencv" alt="OpenCV" />
    <img src="https://img.shields.io/badge/ML-Scikit--Learn-orange?style=for-the-badge&logo=scikit-learn" alt="Scikit-Learn" />
  </div>
</div>

<br/>

## 🌟 Features

### 🧩 Sudoku OCR & Solver
- **Universal Background Extraction**: Capable of reading puzzles from both physical paper (light backgrounds) and digital screenshots (dark UI themes).
- **Robust Digit Recognition**: Uses a custom-trained multi-layer perceptron (MLP) neural network trained on over 3000 synthetic font variations to distinguish difficult numbers (like serif `1` vs `3` or `7`).
- **Precision Grid Warping**: Automatically finds the Sudoku boundary and uses a 4-point perspective transform to "flatten" skewed camera angles.
- **Lightning-fast Backtracking**: Solves the extracted matrix instantaneously and projects it back to the beautiful dark-themed UI.

### 🎲 Rubik's Cube Scanner & Solver
- **Real-Time Camera Integration**: Capture cube faces right from your laptop or phone camera.
- **Dynamic HSV Color Processing**: Extracts color channels, intelligently grouping light artifacts and shadows into standard Rubik's notation (W, Y, R, O, G, B).
- **Kociemba Algorithm Integration**: Solves any valid scrambled 3x3 Rubik's cube configuration in 24 moves or less.
- **Interactive Move Playback**: Provides an easy-to-read sequence of moves (e.g. `R`, `U'`, `F2`) required to solve the cube.

---

## 🛠️ Architecture

Camera Solver is divided into a robust Python backend and a responsive Javascript frontend.

- **Backend (`/backend`)**: Built with **FastAPI**. It handles all the heavy lifting, including:
  - OpenCV image processing (Canny edge detection, Contour grouping, perspective transforms)
  - Sklearn digit classification pipeline
  - Algorithmic solvers for Sudoku (Backtracking) and Kociemba algorithms for the Rubik's Cube.
- **Frontend (`/frontend`)**: Built with **React** & **Vite**. Offers a sleek, responsive, dark-mode focused UI. It handles webcam feeds, image uploads, and rendering the solutions nicely.

---

## 🚀 Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+

### 1. Start the Backend server

```bash
cd backend
pip install -r ../requirements.txt 
python main.py
```
> *The backend will start running on port `8000`*

### 2. Start the Frontend client

Open a new terminal window:
```bash
cd frontend
npm install
npm run dev
```
> *The frontend will start running on port `5173`*

Navigate to `http://localhost:5173` in your browser to start solving!

---

## 🧠 Under the Hood (Computer Vision)

**Sudoku Extraction Pipeline:**
1. **Gaussian Blur & Adaptive Thresholding** to highlight strong edges while ignoring lighting gradients.
2. **Contour Extraction & Area verification** to isolate the 9x9 parent grid.
3. **Four-Point Perspective Transform** to normalize the skewed rectangle into a perfect top-down view.
4. **Cell Iteration & Aggressive Margin Cropping** inside each of the 81 cells to surgically remove grid-lines.
5. **Shape Analysis (Aspect Ratio, Area metrics)** to filter out pencil-marks, dirt, or lighting noise.
6. **ML Classification** of bounding boxes using our custom `digit_ml.py` neural network.

---

<div align="center">
  <i>Built to make solving puzzles magical with the power of Machine Learning.</i>
</div>
