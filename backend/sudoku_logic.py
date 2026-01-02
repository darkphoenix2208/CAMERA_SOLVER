def is_valid(board, row, col, num):
    # Check Row
    for x in range(9):
        if board[row][x] == num:
            return False
            
    # Check Col
    for x in range(9):
        if board[x][col] == num:
            return False
            
    # Check 3x3 Box
    start_row = row - row % 3
    start_col = col - col % 3
    for i in range(3):
        for j in range(3):
            if board[i + start_row][j + start_col] == num:
                return False
                
    return True

def solve_sudoku_backtracking(board):
    """
    Solves the sudoku using backtracking.
    Board is a 9x9 list of lists of integers. 0 represents empty.
    Modifies board in-place.
    Returns True if solved, False if unsolvable.
    """
    for i in range(9):
        for j in range(9):
            if board[i][j] == 0:
                for num in range(1, 10):
                    if is_valid(board, i, j, num):
                        board[i][j] = num
                        if solve_sudoku_backtracking(board):
                            return True
                        board[i][j] = 0
                return False
    return True

    return True

def solve_sudoku(board):
    # Create a deep copy to avoid mutating original if needed externally, 
    # but here we just want to return a new solved board.
    import copy
    board_copy = copy.deepcopy(board)
    if solve_sudoku_backtracking(board_copy):
        return board_copy
    return None

import cv2
import numpy as np
import imutils
from imutils.perspective import four_point_transform
import pytesseract

# Set Tesseract CMD path if not in PATH
# Common Windows paths:
# pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
# We will try to rely on PATH or standard install. If it fails, the API will catch the error.

def find_puzzle(image):
    # Convert to grayscale and blur
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    
    # Adaptive Thresholding to find lines
    # 11, 2 are standard but might fail on soft lighting. 
    thresh = cv2.adaptiveThreshold(blurred, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
    thresh = cv2.bitwise_not(thresh)
    
    # Check if we need to dilate to connect broken lines
    # A simple 3x3 kernel dilation can fix gaps
    kernel = np.ones((3,3), np.uint8)
    thresh = cv2.dilate(thresh, kernel, iterations=1)
    
    # Find contours
    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)
    
    puzzleCnt = None
    total_area = image.shape[0] * image.shape[1]
    
    # Loop over contours to find the grid (largest 4-sided polygon)
    for c in cnts:
        area = cv2.contourArea(c)
        if area < (total_area * 0.1): # Must be at least 10% of image
            continue
            
        peri = cv2.arcLength(c, True)
        
        # Try different levels of approximation to find a 4-sided polygon
        # 0.02 is standard, higher means more simplification (smoothing jagged edges)
        found_approx = None
        for eps in [0.02, 0.03, 0.04, 0.05, 0.08]:
            approx = cv2.approxPolyDP(c, eps * peri, True)
            if len(approx) == 4:
                found_approx = approx
                break
                
        if found_approx is not None:
            # Aspect Ratio Check
            (x, y, w, h) = cv2.boundingRect(found_approx)
            ar = w / float(h)
            
            if 0.5 <= ar <= 2.0:
                puzzleCnt = found_approx
                break
            
    if puzzleCnt is None:
        raise Exception("Could not find Sudoku grid in image")
        
    # Apply perspective transform to get a top-down view
    warped = four_point_transform(gray, puzzleCnt.reshape(4, 2))
    # Also warp the color image for debug/display if needed, but we only need gray for OCR
    return warped, puzzleCnt

def extract_digit(cell):
    # Threshold the cell to get the digit
    # We want text to be foreground (White) for contour analysis
    thresh = cv2.threshold(cell, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    
    # Clear borders (remove grid lines)
    h, w = thresh.shape
    margin = int(h * 0.15) # Increase margin slightly to remove grid borders
    thresh = thresh[margin:h-margin, margin:w-margin]
    
    # Check if there is enough "ink" to be a digit
    total_pixels = thresh.shape[0] * thresh.shape[1]
    white_pixels = cv2.countNonZero(thresh)
    
    if white_pixels < (total_pixels * 0.02): # Lower threshold for thin fonts (2%)
        return 0
        
    # Find the largest connected component (the digit) to center it
    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    
    if len(cnts) == 0:
        return 0
        
    c = max(cnts, key=cv2.contourArea)
    mask = np.zeros(thresh.shape, dtype="uint8")
    cv2.drawContours(mask, [c], -1, 255, -1)
    
    # Clean noise?
    # percentage of mask?
    # For now, let's just use the mask as the digit image
    
    # Now, Tesseract likes BLACK text on WHITE background.
    # Our 'thresh' (and 'mask') is White text on Black.
    # So we must invert it for OCR.
    digit_img = cv2.bitwise_not(mask)
    
    # Resize to standard size
    digit_img = cv2.resize(digit_img, (28, 28))
    
    # Add border (padding)
    digit_img = cv2.copyMakeBorder(digit_img, 5, 5, 5, 5, cv2.BORDER_CONSTANT, value=(255, 255, 255)) # White border
    
    # Tesseract Config
    # --psm 10 : Single character
    # --oem 3 : Default engine
    
    config = r'--psm 10 --oem 3 -c tessedit_char_whitelist=123456789'
    text = pytesseract.image_to_string(digit_img, config=config)
    text = text.strip()
    
    if text.isdigit() and 1 <= int(text) <= 9:
        return int(text)
        
    return 0

def extract_grid_from_image(image_bytes):
    # Decode image
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    if image is None:
        raise Exception("Invalid image data")
        
    # 1. Find and Warping Board
    warped, contour = find_puzzle(image)
    
    # 2. Extract cells
    # We assume a standard 9x9 grid.
    # Resize warped to a fixed size to make cell extraction easy
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
            digit = extract_digit(cell)
            row.append(digit)
        board.append(row)
        
    return board
