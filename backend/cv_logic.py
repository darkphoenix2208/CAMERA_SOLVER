"""
OpenCV-based Rubik's cube face detection and per-sticker color sampling.
"""
import cv2
import numpy as np


def get_color_name(hsv_pixel, ambient_white=None):
    """
    Returns the color name based on HSV value.
    Updated to handle warm/indoor lighting and accept an optional calibration white point.
    """
    h, s, v = hsv_pixel
    
    # 1. Check against ambient calibration (if provided)
    if ambient_white is not None:
        aw_h, aw_s, aw_v = ambient_white
        dh = min(abs(h - aw_h), 180 - abs(h - aw_h))
        ds = abs(s - aw_s)
        
        # If it closely matches the calibrated ambient white 
        # (even if hue is yellow/orange due to warm bulbs)
        if ds < 40 and v > 100 and (s < 50 or dh < 30):
            return 'W'

    # 2. Robust Static Thresholds
    # White: In warm light, saturation can creep up to ~80.
    if s < 75 and v > 110:
        return 'W'
        
    # Yellow: Hue 22-45. True yellow is highly saturated.
    if 22 <= h <= 45:
        if s > 100:
            return 'Y'
        elif v > 120:
            return 'W' # Pale yellow is likely white under warm light
            
    # Orange: Hue 8-22
    if 8 <= h < 22: 
        if s > 110:
            return 'O'
        elif v > 120 and s < 75:
            return 'W'
            
    # Red: Hue 0-8 or 165-180 (Wraps around)
    if h < 8 or h >= 165:
        if s > 100:
            return 'R'
            
    # Green: Hue 45-85
    if 45 <= h < 85:
        return 'G'
        
    # Blue: Hue 85-140
    if 85 <= h < 140:
        return 'B'
        
    # Fallback / outlier
    return 'U'


def detect_cube_face(image, ambient_white=None):
    """
    Analyzes an image frame to detect a 3x3 Rubik's Cube face.
    Optionally accepts an ambient_white HSV array for better color accuracy.
    """
    output_img = image.copy()
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    canny = cv2.Canny(blurred, 50, 150)
    
    height, width = image.shape[:2]
    kernel_size = int(min(height, width) / 25) 
    if kernel_size % 2 == 0: kernel_size += 1
    if kernel_size < 3: kernel_size = 3
    
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (kernel_size, kernel_size))
    dilated = cv2.dilate(canny, kernel)
    
    contours, _ = cv2.findContours(dilated, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    
    candidates = []
    total_image_area = height * width
    
    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area < 1000: continue
        
        perimeter = cv2.arcLength(cnt, True)
        approx = cv2.approxPolyDP(cnt, 0.02 * perimeter, True)
        
        if len(approx) == 4:
            x, y, w, h_rect = cv2.boundingRect(approx)
            aspect_ratio = float(w) / h_rect
            if 0.6 <= aspect_ratio <= 1.5:
                candidates.append((area, approx))
    
    candidates.sort(key=lambda x: x[0], reverse=True)
    
    face_found = False
    detected_colors = []
    center_hsv = None
    
    for area, approx in candidates:
        if area < (total_image_area * 0.05) or area > (total_image_area * 0.95):
            continue
            
        face_contour = approx
        face_found = True
        
        pts = face_contour.reshape(4, 2)
        rect = np.zeros((4, 2), dtype="float32")
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)] # TL
        rect[2] = pts[np.argmax(s)] # BR
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)] # TR
        rect[3] = pts[np.argmax(diff)] # BL
        
        tl, tr, br, bl = rect
        
        def interpolate(p1, p2, t): return p1 + (p2 - p1) * t
        
        for r in range(3):
            for c in range(3):
                top_x = interpolate(tl, tr, (c + 0.5) / 3.0)
                bot_x = interpolate(bl, br, (c + 0.5) / 3.0)
                center_point = interpolate(top_x, bot_x, (r + 0.5) / 3.0)
                
                cx, cy = int(center_point[0]), int(center_point[1])
                
                cv2.circle(output_img, (cx, cy), 5, (0, 0, 0), 2)
                cv2.circle(output_img, (cx, cy), 3, (255, 255, 255), -1)
                
                y_min, y_max = max(0, cy-5), min(height, cy+5)
                x_min, x_max = max(0, cx-5), min(width, cx+5)
                
                roi = hsv_image[y_min:y_max, x_min:x_max]
                if roi.size > 0:
                    avg_hsv = np.mean(roi, axis=(0, 1))
                    color_code = get_color_name(avg_hsv, ambient_white)
                    if r == 1 and c == 1:
                        center_hsv = avg_hsv.tolist()
                else:
                    color_code = 'U'
                
                detected_colors.append(color_code)
                cv2.putText(output_img, color_code, (cx-5, cy-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        cv2.drawContours(output_img, [face_contour], -1, (0, 255, 0), 3)
        break

    return output_img, face_found, detected_colors, center_hsv
