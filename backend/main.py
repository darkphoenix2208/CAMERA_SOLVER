import sys
import types
import os

# Monkey-patch 'imp' module for Python 3.12+ compatibility (required by rubik_solver/future)
try:
    import imp
except ImportError:
    import importlib
    import importlib.util
    
    # Create a dummy module
    imp = types.ModuleType('imp')
    sys.modules['imp'] = imp
    
    # Map necessary functions
    imp.reload = importlib.reload
    imp.find_module = lambda name, path=None: (None, None, None) # Mock
    # If they use other imp functions, we might need more mocks.

from fastapi import FastAPI, UploadFile, File
import uvicorn
import cv2
import numpy as np
import base64
from fastapi.middleware.cors import CORSMiddleware
import sys
import os

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

from rubik_solver.utils import solve as solve_cube
from pydantic import BaseModel
from typing import List, Dict

class CubeState(BaseModel):
    # Keys should be 'U', 'L', 'F', 'R', 'B', 'D' (standard notation)
    # Values should be list of 9 color codes ['W', 'W', ...]
    faces: Dict[str, List[str]]

@app.post("/solve")
def solve_cube_endpoint(state: CubeState):
    try:
        # rubik_solver expects string of 54 chars: U1...U9 R1...R9 F1...F9 D1...D9 L1...L9 B1...B9
        # WAIT: The library documentation says order is URFDLB? Or similar?
        # Let's check standard. 
        # Standard notation usually: U, R, F, D, L, B ?
        # Actually rubik_solver usually follows:
        # UUUUUUUUU RRRRRRRRR FFFFFFFFF DDDDDDDDD LLLLLLLLL BBBBBBBBB
        
        # We will assume our frontend sends them in this dict:
        # { 'U': [], 'R': [], 'F': [], 'D': [], 'L': [], 'B': [] }
        
        # NOTE: Colors must be mapped to the actual side names U, R, F, D, L, B.
        # Ideally the Solver just cares about the permutation.
        # If Central 'W' is Up, then all 'W' stickers are 'U'.
        # We need to map colors to faces.
        
        # Step 1: Determine map based on centers (index 4 of each face)
        # e.g. center of 'U' face is detected as 'W', so 'W' -> 'U'
        
        color_to_side_map = {}
        for face_name, colors in state.faces.items():
            center_color = colors[4] # Center sticker
            color_to_side_map[center_color] = face_name
            
        # If we have duplicate centers or missing colors, it might fail.
        # But let's proceed optimistically.
        
        full_string = ""
        # The specific order rubik_solver expects is U, L, F, R, B, D based on some sources, 
        # BUT commonly it is U-L-F-R-B-D or U-R-F-D-L-B.
        # Let's assume U-L-F-R-B-D order for the string construction based on Kociemba standard which usually is U, R, F, D, L, B.
        # ACTUALLY: 'rubik_solver' library uses:
        # ybr ybr ybr (Yellow=U?) it depends.
        # Safest is to just pass the raw color chars if we map them correctly?
        # No, solve() takes a string of moves OR state.
        # State encoding: "wowgyb..."
        
        # Let's try to map the colors to side chars U, D, L, R, F, B
        # And construct the string in order: U, L, F, R, B, D  <-- This order matters for the string representation?
        
        # Correct order for Kociemba solver string is usually:
        # U1..U9, R1..R9, F1..F9, D1..D9, L1..L9, B1..B9
        
        order = ['U', 'R', 'F', 'D', 'L', 'B']
        
        for face in order:
            if face not in state.faces:
                return {"success": False, "error": f"Missing face {face}"}
            
            face_colors = state.faces[face]
            # Convert colors to side notation
            # e.g. if 'W' is on U-face, 'W' becomes 'U'
            for c in face_colors:
                if c in color_to_side_map:
                    full_string += color_to_side_map[c]
                else:
                    # Fallback or error?
                    full_string += 'U' # Dummy
                    
        # Solve
        # Method 'Kociemba' is fast and optimal
        solution_moves = solve_cube(full_string, 'Kociemba')
        
        # Convert moves (objects) to string list
        solution_strs = [str(m) for m in solution_moves]
        
        return {
            "success": True,
            "solution": solution_strs,
            "debug_string": full_string
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
