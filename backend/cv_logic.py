    # ... (previous code) ...

def get_color_name(hsv_pixel):
    """
    Returns the color name based on HSV value.
    Ranges are empirical and might need tuning or dynamic calibration.
    """
    h, s, v = hsv_pixel
    
    # Check Grayscale/Achroamtic first (White/Black/Grey)
    # White: Low saturation, High Value
    if s < 50 and v > 150:
        return 'W'
        
    # Yellow is often tricky vs White in bright light, but usually has S > 50
    # Yellow Hue is around 20-35 (OpenCV H is 0-179)
    if 20 <= h <= 40: # Yellow
        return 'Y'
        
    # Orange: 5-20 or 160-179 (wrap around, but usually simplified)
    if 5 <= h < 20: 
        return 'O'
        
    # Red: 0-5 or 160-180
    if h < 5 or h >= 160:
        return 'R'
        
    # Green: 40-90
    if 40 <= h < 90:
        return 'G'
        
    # Blue: 90-130
    if 90 <= h < 130:
        return 'B'
        
    # Fallback / outlier
    return 'U' # Unknown

def detect_cube_face(image):
    """
    Analyzes an image frame to detect a 3x3 Rubik's Cube face.
    """
    output_img = image.copy()
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    canny = cv2.Canny(blurred, 50, 150)
    
    # Dynamic Kernel Size based on image resolution
    # For a 1000px wide image, we want a kernel that bridges the sticker gaps.
    # A standard sticker gap is maybe 1/30th of the face width?
    # Let's be aggressive.
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
            x, y, w, h = cv2.boundingRect(approx)
            aspect_ratio = float(w) / h
            # Loose aspect ratio to allow for perspective
            if 0.6 <= aspect_ratio <= 1.5:
                candidates.append((area, approx))
    
    candidates.sort(key=lambda x: x[0], reverse=True)
    height, width = image.shape[:2]
    total_image_area = height * width
    
    face_found = False
    detected_colors = []
    
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
        
        # We need grid centers to sample colors
        # cell (r, c) center is average of its 4 corners
        # But efficiently: 
        # r=0..2, c=0..2. Center is at (r+0.5)/3, (c+0.5)/3 in normalized coords
        
        for r in range(3):
            for c in range(3):
                # Calculate approximate center of the cell in perspective
                # Interpolate Top and Bottom edges at (c+0.5)/3
                top_x = interpolate(tl, tr, (c + 0.5) / 3.0)
                bot_x = interpolate(bl, br, (c + 0.5) / 3.0)
                
                # Interpolate along that vertical line at (r+0.5)/3
                center_point = interpolate(top_x, bot_x, (r + 0.5) / 3.0)
                cx, cy = int(center_point[0]), int(center_point[1])
                
                # Draw sample point
                cv2.circle(output_img, (cx, cy), 5, (0, 0, 0), 2)
                cv2.circle(output_img, (cx, cy), 3, (255, 255, 255), -1)
                
                # Sample Color (Average of 5x5 region around center)
                # Ensure bounds
                y_min, y_max = max(0, cy-5), min(height, cy+5)
                x_min, x_max = max(0, cx-5), min(width, cx+5)
                
                roi = hsv_image[y_min:y_max, x_min:x_max]
                if roi.size > 0:
                    # Average HSV
                    avg_hsv = np.mean(roi, axis=(0, 1))
                    color_code = get_color_name(avg_hsv)
                else:
                    color_code = 'U'
                
                detected_colors.append(color_code)
                
                # Draw color text
                cv2.putText(output_img, color_code, (cx-5, cy-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Draw grid lines for visualization (simplified from before)
        cv2.drawContours(output_img, [face_contour], -1, (0, 255, 0), 3)
        
        # Break after finding the best face
        break

    return output_img, face_found, detected_colors

