import pytest
from fastapi.testclient import TestClient
import numpy as np
import cv2
import sys
import os

# Add parent directory to path to import main
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import app

client = TestClient(app)

def test_solve_sudoku_valid():
    # A known easy sudoku board
    board = [
        [5, 3, 0, 0, 7, 0, 0, 0, 0],
        [6, 0, 0, 1, 9, 5, 0, 0, 0],
        [0, 9, 8, 0, 0, 0, 0, 6, 0],
        [8, 0, 0, 0, 6, 0, 0, 0, 3],
        [4, 0, 0, 8, 0, 3, 0, 0, 1],
        [7, 0, 0, 0, 2, 0, 0, 0, 6],
        [0, 6, 0, 0, 0, 0, 2, 8, 0],
        [0, 0, 0, 4, 1, 9, 0, 0, 5],
        [0, 0, 0, 0, 8, 0, 0, 7, 9]
    ]
    response = client.post("/solve-sudoku", json={"board": board})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "solution" in data
    # Verify the first empty cell was solved (0,2 is 4)
    assert data["solution"][0][2] == 4

def test_solve_sudoku_empty():
    # Edge case: empty board
    board = [[0]*9 for _ in range(9)]
    response = client.post("/solve-sudoku", json={"board": board})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "solution" in data

def test_solve_sudoku_invalid():
    # Edge case: invalid board
    board = [
        [5, 5, 0, 0, 7, 0, 0, 0, 0], # Two 5s in first row
        [6, 0, 0, 1, 9, 5, 0, 0, 0],
        [0, 9, 8, 0, 0, 0, 0, 6, 0],
        [8, 0, 0, 0, 6, 0, 0, 0, 3],
        [4, 0, 0, 8, 0, 3, 0, 0, 1],
        [7, 0, 0, 0, 2, 0, 0, 0, 6],
        [0, 6, 0, 0, 0, 0, 2, 8, 0],
        [0, 0, 0, 4, 1, 9, 0, 0, 5],
        [0, 0, 0, 0, 8, 0, 0, 7, 9]
    ]
    response = client.post("/solve-sudoku", json={"board": board})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == False
    assert "error" in data

def test_solve_rubiks_valid():
    # U move scrambled cube
    scrambled_faces = {
        "U": ["W"]*9,
        "R": ["B","B","B", "R","R","R", "R","R","R"],
        "F": ["R","R","R", "G","G","G", "G","G","G"],
        "D": ["Y"]*9,
        "L": ["G","G","G", "O","O","O", "O","O","O"],
        "B": ["O","O","O", "B","B","B", "B","B","B"]
    }
    response = client.post("/solve", json={"faces": scrambled_faces})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == True
    assert "solution" in data
    assert len(data["solution"]) > 0

def test_solve_rubiks_incomplete():
    # Missing a face
    faces = {
        "U": ["W"]*9,
        "R": ["R"]*9,
        "F": ["G"]*9,
        "D": ["Y"]*9,
        "L": ["O"]*9
    }
    response = client.post("/solve", json={"faces": faces})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == False
    assert "error" in data

def create_dummy_image_bytes():
    img = np.ones((480, 640, 3), dtype=np.uint8) * 255
    _, encoded = cv2.imencode('.jpg', img)
    return encoded.tobytes()

def test_extract_sudoku_invalid_image():
    response = client.post("/extract-sudoku", files={"file": ("test.txt", b"not an image", "text/plain")})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == False
    assert "error" in data

def test_extract_sudoku_empty_image():
    img_bytes = create_dummy_image_bytes()
    response = client.post("/extract-sudoku", files={"file": ("img.jpg", img_bytes, "image/jpeg")})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == False
    assert "error" in data

def test_detect_face_empty_image():
    img_bytes = create_dummy_image_bytes()
    response = client.post("/detect-face", files={"file": ("img.jpg", img_bytes, "image/jpeg")})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == False
    assert "colors" in data
    assert len(data["colors"]) == 0

def test_detect_face_malformed():
    response = client.post("/detect-face", files={"file": ("test.txt", b"bad", "text/plain")})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] == False
    assert "error" in data
