import sys
import os
import time
import json
import logging
from datetime import datetime

# Configure Logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

from fastapi import FastAPI, UploadFile, File, Form
import uvicorn
import cv2
import numpy as np
import base64
from fastapi.middleware.cors import CORSMiddleware

# Add current directory to path to find cv_logic
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from cv_logic import detect_cube_face

app = FastAPI()

# Allow CORS for React frontend (usually runs on port 5173 or 3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For dev, allow all
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"status": "Backend is running"}

@app.post("/detect-face")
async def detect_face_endpoint(
    file: UploadFile = File(...),
    ambient_white: str = Form(None)
):
    # Read image content
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if image is None:
        logger.error("Detect Face: Invalid image data received.")
        return {"success": False, "error": "Invalid image data"}
        
    aw = None
    if ambient_white:
        try:
            aw = [int(x.strip()) for x in ambient_white.split(",")]
        except:
            pass

    # Run logic
    processed_img, face_found, detected_colors, center_hsv = detect_cube_face(image, ambient_white=aw)
    
    # Encode processed image back to base64 to send to frontend for display
    _, buffer = cv2.imencode('.jpg', processed_img)
    img_base64 = base64.b64encode(buffer).decode('utf-8')
    
    if face_found:
        logger.info(f"Detect Face: Success. Colors: {detected_colors}")
    else:
        logger.info("Detect Face: No face found in image.")
    
    return {
        "success": face_found,
        "image": f"data:image/jpeg;base64,{img_base64}",
        "message": "Face detected" if face_found else "No face detected",
        "colors": detected_colors,
        "center_hsv": center_hsv
    }

from pydantic import BaseModel
from typing import List, Dict

from kociemba_pkg import solve_kociemba

class CubeState(BaseModel):
    # Keys 'U','R','F','D','L','B'; values are 9 sticker color codes W,Y,R,O,G,B (see wizard).
    faces: Dict[str, List[str]]


def _kociemba_facelet_string(state: CubeState) -> str:
    """54 chars: U then R then F then D then L then B; each char is U,R,F,D,L,B by sticker colour."""
    color_to_face = {}
    for face in ["U", "R", "F", "D", "L", "B"]:
        color_to_face[state.faces[face][4]] = face
    order = ["U", "R", "F", "D", "L", "B"]
    out = []
    for face in order:
        for sticker in state.faces[face]:
            ch = color_to_face.get(sticker)
            if ch is None:
                raise ValueError(f"Unknown sticker colour {sticker!r}; fix centres or taps.")
            out.append(ch)
    return "".join(out)


@app.post("/solve")
def solve_cube_endpoint(state: CubeState):
    try:
        for face in ["U", "R", "F", "D", "L", "B"]:
            if face not in state.faces:
                return {"success": False, "error": f"Missing face {face}"}
            if len(state.faces[face]) != 9:
                return {"success": False, "error": f"Face {face} must have 9 stickers"}

        cubestring = _kociemba_facelet_string(state)
        
        start_time = time.perf_counter()
        solution_str = solve_kociemba(cubestring)
        solve_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
        
        solution_strs = [m for m in solution_str.split() if m]

        logger.info(f"Solve Rubik's: Success. Time: {solve_time_ms}ms")
        return {
            "success": True,
            "solution": solution_strs,
            "debug_string": cubestring,
            "solve_time_ms": solve_time_ms
        }

    except Exception as e:
        logger.error(f"Solve Rubik's Error: {str(e)}", exc_info=True)
        return {"success": False, "error": str(e)}

# --- Sudoku Endpoint ---
from sudoku_logic import solve_sudoku, extract_grid_from_image

class SudokuBoard(BaseModel):
    board: List[List[int]] # 9x9 grid, 0 for empty

@app.post("/extract-sudoku")
async def extract_sudoku_endpoint(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        board, corners, confidence = extract_grid_from_image(contents)
        logger.info(f"Extract Sudoku: Found board with confidence {confidence:.2f}")
        return {"success": True, "board": board, "corners": corners, "confidence": confidence}
    except Exception as e:
        msg = str(e)
        logger.error(f"Extract Sudoku Error: {msg}", exc_info=True)
        if "tesseract is not installed" in msg.lower() or "files" in msg.lower():
            return {"success": False, "error": "Server missing OCR (Tesseract). Process manually."}
        return {"success": False, "error": msg}

@app.post("/solve-sudoku")
def solve_sudoku_endpoint(data: SudokuBoard):
    try:
        start_time = time.perf_counter()
        solution = solve_sudoku(data.board)
        solve_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
        
        if solution:
            logger.info(f"Solve Sudoku: Success. Time: {solve_time_ms}ms")
            return {"success": True, "solution": solution, "solve_time_ms": solve_time_ms}
        else:
            logger.error("Solve Sudoku: Unsolvable board")
            return {"success": False, "error": "Unsolvable board"}
    except Exception as e:
        logger.error(f"Solve Sudoku Error: {str(e)}", exc_info=True)
        return {"success": False, "error": str(e)}

class Feedback(BaseModel):
    puzzle_type: str
    was_correct: bool

@app.post("/log-feedback")
def log_feedback_endpoint(data: Feedback):
    log_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "accuracy_log.json")
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "puzzle_type": data.puzzle_type,
        "was_correct": data.was_correct
    }
    
    logs = []
    if os.path.exists(log_file):
        try:
            with open(log_file, "r") as f:
                logs = json.load(f)
        except Exception:
            pass
            
    logs.append(entry)
    
    with open(log_file, "w") as f:
        json.dump(logs, f, indent=2)
        
    logger.info(f"Feedback Logged: {data.puzzle_type} - Correct: {data.was_correct}")
    return {"success": True}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
