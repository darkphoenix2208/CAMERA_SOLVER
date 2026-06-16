from __future__ import annotations

# ──────────────────────────────────────────────────────────────────────────────
# SOLVER  (unchanged)
# ──────────────────────────────────────────────────────────────────────────────

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


def solve_sudoku(board):
    import copy
    board_copy = copy.deepcopy(board)
    if solve_sudoku_backtracking(board_copy):
        return board_copy
    return None


# ──────────────────────────────────────────────────────────────────────────────
# IMAGE EXTRACTION — rewritten for universal background support
# ──────────────────────────────────────────────────────────────────────────────

import cv2
import numpy as np
import imutils
from imutils.perspective import four_point_transform

try:
    import pytesseract
except ImportError:
    pytesseract = None


# ---------------------------------------------------------------------------
# 1.  FIND THE PUZZLE GRID
# ---------------------------------------------------------------------------

def find_puzzle(image):
    """Locate the largest square-ish contour — the Sudoku grid outline."""
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (7, 7), 3)

    # Adaptive threshold to pull out the grid lines
    thresh = cv2.adaptiveThreshold(
        blurred, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2,
    )
    thresh = cv2.bitwise_not(thresh)

    # Light dilation to connect broken grid lines
    kernel = np.ones((3, 3), np.uint8)
    thresh = cv2.dilate(thresh, kernel, iterations=1)

    # Find external contours, sorted largest first
    cnts = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)

    puzzleCnt = None
    total_area = image.shape[0] * image.shape[1]

    for c in cnts:
        area = cv2.contourArea(c)
        if area < (total_area * 0.1):
            continue

        peri = cv2.arcLength(c, True)
        found_approx = None
        for eps in [0.02, 0.03, 0.04, 0.05, 0.08]:
            approx = cv2.approxPolyDP(c, eps * peri, True)
            if len(approx) == 4:
                found_approx = approx
                break

        if found_approx is not None:
            (x, y, w, h) = cv2.boundingRect(found_approx)
            ar = w / float(h)
            if 0.5 <= ar <= 2.0:
                puzzleCnt = found_approx
                break

    if puzzleCnt is None:
        raise Exception("Could not find Sudoku grid in image")

    warped = four_point_transform(gray, puzzleCnt.reshape(4, 2))
    return warped, puzzleCnt


# ---------------------------------------------------------------------------
# 2.  CELL-LEVEL HELPERS
# ---------------------------------------------------------------------------

def _cell_texture_var(gray: np.ndarray) -> float:
    """Laplacian variance — high for edges/text, low for flat regions."""
    if gray.size == 0:
        return 0.0
    return float(cv2.Laplacian(gray, cv2.CV_64F).var())


def _likely_empty_cell(gray: np.ndarray) -> bool:
    """
    Determine whether a cell is empty.
    Works on *both* light (paper) and dark (UI) backgrounds.
    """
    if gray.size == 0:
        return True

    mn = float(np.mean(gray))
    sd = float(np.std(gray))
    lv = _cell_texture_var(gray)

    # ── Very uniform cell (any background) ──
    if sd < 8.0 and lv < 15.0:
        return True

    # ── Light background (paper) ──
    if mn > 160.0:
        if sd < 22.0 and lv < 60.0:
            return True

    # ── Dark background (UI) ──
    if mn < 50.0:
        if sd < 12.0 and lv < 35.0:
            return True

    # ── Foreground-pixel density check ──
    g = cv2.GaussianBlur(gray, (3, 3), 0)
    if mn > 127:
        _, th = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    else:
        _, th = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        if np.mean(th) > 127:
            th = cv2.bitwise_not(th)

    fill_ratio = np.count_nonzero(th) / max(th.size, 1)
    if fill_ratio < 0.02:
        return True

    return False


def _binarize_for_ocr(gray: np.ndarray):
    """
    Binarize cell and find the *best* digit-shaped contour.
    Returns (binary_image, contour | None).
    Applies strict size / shape / position filters to reject grid-line
    fragments, pencil marks, and other noise.
    """
    H, W = gray.shape[:2]
    cell_area = H * W

    g = cv2.GaussianBlur(gray, (3, 3), 0)
    med = float(np.median(g))

    # Threshold (white foreground = digit pixels)
    if med < 120:
        _, th = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        if np.mean(th) > 127:
            th = cv2.bitwise_not(th)
    else:
        _, th = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    k = np.ones((2, 2), np.uint8)
    th = cv2.morphologyEx(th, cv2.MORPH_CLOSE, k, iterations=1)

    cnts = cv2.findContours(th.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = imutils.grab_contours(cnts)
    if not cnts:
        return th, None

    # ── Strict contour filtering ──
    valid = []
    for c in cnts:
        area = cv2.contourArea(c)
        if area < cell_area * 0.03:          # ≥ 3 % of cell (was 1.2 %)
            continue

        x, y, w, h = cv2.boundingRect(c)

        if h < H * 0.28:                     # height ≥ 28 % of cell
            continue
        if w < W * 0.10:                      # width ≥ 10 %
            continue

        aspect = w / max(h, 1)
        if aspect > 2.5:                      # reject wide/flat line fragments
            continue
        if aspect < 0.06:                     # reject hairline-thin artefacts
            continue

        # Centroid must sit in the inner ~70 % of the cell
        cx = x + w / 2.0
        cy = y + h / 2.0
        mx = W * 0.15
        my = H * 0.15
        if cx < mx or cx > W - mx or cy < my or cy > H - my:
            continue

        valid.append(c)

    if not valid:
        return th, None

    best = max(valid, key=cv2.contourArea)
    return th, best


def _crop_for_ml(gray: np.ndarray, contour) -> np.ndarray:
    """Tight crop around contour bbox → normalised to white-on-black."""
    x, y, cw, ch = cv2.boundingRect(contour)
    pad = max(3, min(cw, ch) // 6)
    H, W = gray.shape[:2]
    x0, y0 = max(0, x - pad), max(0, y - pad)
    x1, y1 = min(W, x + cw + pad), min(H, y + ch + pad)
    crop = gray[y0:y1, x0:x1]
    if crop.size == 0:
        return gray
    m = float(np.median(crop))
    if m > 130:
        crop = 255 - crop
    return crop


def _aspect_ratio(contour) -> float:
    x, y, w, h = cv2.boundingRect(contour)
    if h < 1:
        return 1.0
    return float(w) / float(h)


def _fix_7_vs_1(pred: int, ar: float, second: tuple[int, float]) -> int:
    """Narrow vertical stroke → 1 ; wide cap → 7."""
    d2, p2 = second
    if pred == 7 and ar < 0.32 and d2 == 1 and p2 > 0.2:
        return 1
    if pred == 1 and ar > 0.52 and d2 == 7 and p2 > 0.25:
        return 7
    return pred


def _fix_narrow_digit(pred: int, ar: float) -> int:
    if pred == 7 and ar < 0.33:
        return 1
    if pred == 3 and ar < 0.35:
        return 1
    return pred


def _fix_3_vs_1(pred: int, ar: float, second: tuple[int, float]) -> int:
    """Serif/narrow 1s often misread as 3. AR < 0.38 strongly suggests 1."""
    d2, p2 = second
    if pred == 3 and ar < 0.38 and d2 == 1 and p2 > 0.10:
        return 1
    if pred == 3 and ar < 0.30:   # extremely narrow → definitely 1
        return 1
    if pred == 1 and ar > 0.55 and d2 == 3 and p2 > 0.25:
        return 3
    return pred

def _fix_3_vs_8(pred: int, roi: np.ndarray, second: tuple[int, float]) -> int:
    """8 has a higher pixel density (closed loops) compared to 3."""
    d2, p2 = second
    if pred in (3, 8) and p2 > 0.15:
        density = np.count_nonzero(roi > 127) / max(roi.size, 1)
        if pred == 3 and d2 == 8 and density > 0.38:
            return 8
        if pred == 8 and d2 == 3 and density < 0.31:
            return 3
    return pred

def _fix_5_vs_6(pred: int, roi: np.ndarray, second: tuple[int, float]) -> int:
    """6 usually has a closed bottom loop making it overall denser than 5."""
    d2, p2 = second
    if pred in (5, 6) and p2 > 0.15:
        density = np.count_nonzero(roi > 127) / max(roi.size, 1)
        if pred == 5 and d2 == 6 and density > 0.39:
            return 6
        if pred == 6 and d2 == 5 and density < 0.32:
            return 5
    return pred


# ---------------------------------------------------------------------------
# 3.  OCR HELPERS
# ---------------------------------------------------------------------------

def _tesseract_digit(ocr_img: np.ndarray) -> int:
    if pytesseract is None:
        return 0
    try:
        config = r"--psm 10 --oem 3 -c tessedit_char_whitelist=123456789"
        text = pytesseract.image_to_string(ocr_img, config=config).strip()
        if len(text) >= 1 and text[0].isdigit():
            v = int(text[0])
            if 1 <= v <= 9:
                return v
    except Exception:
        pass
    return 0


# ---------------------------------------------------------------------------
# 4.  MAIN DIGIT EXTRACTION (per cell)
# ---------------------------------------------------------------------------

def extract_digit(cell):
    """
    Extract a single digit from a cell image.
    Returns (digit, prob) where prob is a confidence score.
    Returns (0, 1.0) for empty cells.
    """
    if cell.size == 0:
        return 0, 1.0

    gray = cell if len(cell.shape) == 2 else cv2.cvtColor(cell, cv2.COLOR_BGR2GRAY)

    # Quick empty-cell filter
    if _likely_empty_cell(gray):
        return 0, 1.0

    # Binarize & find digit contour (strict filtering already applied)
    th, contour = _binarize_for_ocr(gray)
    if contour is None:
        return 0, 1.0                           # no digit-shaped blob → empty

    # Extra height gate
    H, W = gray.shape[:2]
    _, _, _, ch = cv2.boundingRect(contour)
    if ch < H * 0.28:
        return 0, 1.0

    # ── ML prediction (primary path) ──
    ml_roi = _crop_for_ml(gray, contour)
    ar = _aspect_ratio(contour)

    try:
        from digit_ml import predict_digit_top2

        (a, pa), (b, pb) = predict_digit_top2(ml_roi)

        if pa < 0.45:
            return 0, 1.0
        if not (1 <= a <= 9):
            return 0, 1.0

        pred = _fix_7_vs_1(int(a), ar, (int(b), float(pb)))
        pred = _fix_3_vs_1(pred, ar, (int(b), float(pb)))
        pred = _fix_narrow_digit(pred, ar)
        pred = _fix_3_vs_8(pred, ml_roi, (int(b), float(pb)))
        pred = _fix_5_vs_6(pred, ml_roi, (int(b), float(pb)))

        # Low-confidence 7/1 ambiguity → bail
        if pred in (7, 1) and pa < 0.50 and (pa - pb) < 0.08:
            return 0, 1.0

        return pred, float(pa)
    except Exception:
        pass

    # ── Fallback: Tesseract OCR ──
    mask = np.zeros(th.shape, dtype=np.uint8)
    cv2.drawContours(mask, [contour], -1, 255, -1)
    digit_bin = cv2.bitwise_and(th, mask)
    ocr_in = cv2.bitwise_not(digit_bin)
    ocr_in = cv2.resize(ocr_in, (32, 32), interpolation=cv2.INTER_AREA)
    ocr_in = cv2.copyMakeBorder(ocr_in, 6, 6, 6, 6, cv2.BORDER_CONSTANT, value=255)
    res = _tesseract_digit(ocr_in)
    return res, 0.4 if res != 0 else 1.0


# ---------------------------------------------------------------------------
# 5.  FULL GRID EXTRACTION
# ---------------------------------------------------------------------------

def extract_grid_from_image(image_bytes):
    """Extract 9×9 grid of digits from a Sudoku puzzle image."""
    nparr = np.frombuffer(image_bytes, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if image is None:
        raise Exception("Invalid image data")

    # 1. Find and warp the puzzle grid
    warped, _contour = find_puzzle(image)

    # 2. Resize to fixed dimensions
    grid_size = 900
    warped = cv2.resize(warped, (grid_size, grid_size), interpolation=cv2.INTER_AREA)

    # 3. Extract cells with an inward margin to crop out grid lines
    step = grid_size // 9      # 100 px per cell
    margin = 13                # removes ~13 px of grid-line on every edge

    board = []
    total_non_empty = 0
    clean_non_empty = 0

    for y in range(9):
        row = []
        for x in range(9):
            sy = y * step + margin
            ey = (y + 1) * step - margin
            sx = x * step + margin
            ex = (x + 1) * step - margin

            cell = warped[sy:ey, sx:ex]
            digit, prob = extract_digit(cell)
            row.append(digit)
            if digit != 0:
                total_non_empty += 1
                if prob >= 0.70:
                    clean_non_empty += 1
        board.append(row)

    confidence = float(clean_non_empty / total_non_empty) if total_non_empty > 0 else 0.0
    return board, _contour.tolist() if _contour is not None else None, confidence
