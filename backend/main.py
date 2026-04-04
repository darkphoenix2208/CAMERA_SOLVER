import sys
import os

from fastapi import FastAPI, UploadFile, File
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
async def detect_face_endpoint(file: UploadFile = File(...)):
    # Read image content
    contents = await file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if image is None:
        return {"success": False, "error": "Invalid image data"}
        
    # Run logic
    processed_img, face_found, detected_colors = detect_cube_face(image)
    
    # Encode processed image back to base64 to send to frontend for display
    _, buffer = cv2.imencode('.jpg', processed_img)
    img_base64 = base64.b64encode(buffer).decode('utf-8')
    
    return {
        "success": face_found,
        "image": f"data:image/jpeg;base64,{img_base64}",
        "message": "Face detected" if face_found else "No face detected",
        "colors": detected_colors
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
        solution_str = solve_kociemba(cubestring)
        solution_strs = [m for m in solution_str.split() if m]

        return {
            "success": True,
            "solution": solution_strs,
            "debug_string": cubestring,
        }

    except Exception as e:
        return {"success": False, "error": str(e)}

# --- Sudoku Endpoint ---
from sudoku_logic import solve_sudoku, extract_grid_from_image

class SudokuBoard(BaseModel):
    board: List[List[int]] # 9x9 grid, 0 for empty

@app.post("/extract-sudoku")
async def extract_sudoku_endpoint(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        board = extract_grid_from_image(contents)
        return {"success": True, "board": board}
    except Exception as e:
        # Pytesseract error often means not installed
        msg = str(e)
        if "tesseract is not installed" in msg.lower() or "files" in msg.lower():
            return {"success": False, "error": "Server missing OCR (Tesseract). Process manually."}
        return {"success": False, "error": msg}

@app.post("/solve-sudoku")
def solve_sudoku_endpoint(data: SudokuBoard):
    try:
        solution = solve_sudoku(data.board)
        if solution:
            return {"success": True, "solution": solution}
        else:
            return {"success": False, "error": "Unsolvable board"}
    except Exception as e:
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
