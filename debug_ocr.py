import cv2
import numpy as np
import sys
import os
import imutils

# Add backend to path
sys.path.append('backend')
from sudoku_logic import extract_grid_from_image, find_puzzle, extract_digit

def debug_run(image_path):
    print(f"Loading {image_path}...")
    image = cv2.imread(image_path)
    if image is None:
        print("Failed to load image")
        return

    try:
        # Load image locally to debug logic
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        thresh = cv2.adaptiveThreshold(blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        thresh = cv2.bitwise_not(thresh)
        kernel = np.ones((3,3), np.uint8)
        thresh = cv2.dilate(thresh, kernel, iterations=1)
        
        cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        cnts = sorted(cnts, key=cv2.contourArea, reverse=True)
        
        print(f"Total contours found: {len(cnts)}")
        for i, c in enumerate(cnts[:10]):
            area = cv2.contourArea(c)
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            print(f"Contour #{i}: Area={area:.2f}, Vertices={len(approx)}")
            
        # 1. Test find_puzzle (calling the real function)
        warped, contour = find_puzzle(image)
        print("Puzzle found! Warped shape:", warped.shape)
        cv2.imwrite("debug_warped.jpg", warped) 
        
        # 2. Test cell extraction
        warped = cv2.resize(warped, (450, 450))
        step_x = 450 // 9
        step_y = 450 // 9
        
        board = []
        for y in range(9):
            row = []
            for x in range(9):
                start_x = x * step_x
                start_y = y * step_y
                end_x = (x + 1) * step_x
                end_y = (y + 1) * step_y
                cell = warped[start_y:end_y, start_x:end_x]
                
                # Save first few cells for inspection
                if y == 0 and x < 5:
                    cv2.imwrite(f"debug_cell_{y}_{x}.jpg", cell)
                    
                # We need to call extract_digit, but we want to see errors.
                # Let's temporarily call it directly or copy logic?
                # Easiest is to modify the import or jus trust the logging.
                # Actually, I'll copy the extract_digit logic here for full debugging control 
                # OR just wrap the call in a try/except that prints.
                
                try:
                    digit = extract_digit(cell)
                except Exception as e:
                    print(f"OCR Error at {y},{x}: {e}")
                    digit = 0
                    
                row.append(digit)
            board.append(row)
            
        print("Extracted Board:")
        for r in board:
            print(r)
            
    except Exception as e:
        print("Error:", e)

if __name__ == "__main__":
    # Use the path to the uploaded image provided in metadata
    # C:/Users/abhis/.gemini/antigravity/brain/408cd606-baf5-4651-bee6-7f9da3cd3a7c/uploaded_image_2_1766823965987.png
    # I need to handle the path carefully
    path = r"C:\Users\abhis\.gemini\antigravity\brain\408cd606-baf5-4651-bee6-7f9da3cd3a7c\uploaded_image_2_1766823965987.png"
    debug_run(path)
