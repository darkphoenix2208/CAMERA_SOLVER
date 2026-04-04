"""
Digit classifier for Sudoku: trained on synthetic digits covering both
dark-theme (light text on dark bg) and paper (dark text on light bg) styles.
Uses MLPClassifier for better accuracy than LogisticRegression.
"""
from __future__ import annotations

import numpy as np
import cv2

_clf = None


def _augment(canvas: np.ndarray) -> np.ndarray:
    """Light blur, noise, morphological variations to match real images."""
    if np.random.random() < 0.4:
        k = np.random.choice([3, 5])
        canvas = cv2.GaussianBlur(canvas, (k, k), 0)
    if np.random.random() < 0.3:
        noise = np.random.normal(0, np.random.uniform(2, 10), canvas.shape).astype(np.float32)
        canvas = np.clip(canvas.astype(np.float32) + noise, 0, 255).astype(np.uint8)
    if np.random.random() < 0.15:
        k = np.ones((2, 2), np.uint8)
        if np.random.random() < 0.5:
            canvas = cv2.dilate(canvas, k, iterations=1)
        else:
            canvas = cv2.erode(canvas, k, iterations=1)
    return canvas


def _build_training_data(rng: np.random.Generator, n_per_digit: int = 350):
    """Generate synthetic training digits for both dark and light backgrounds."""
    X_list = []
    y_list = []
    fonts = [
        cv2.FONT_HERSHEY_SIMPLEX,
        cv2.FONT_HERSHEY_PLAIN,
        cv2.FONT_HERSHEY_DUPLEX,
        cv2.FONT_HERSHEY_COMPLEX,
        cv2.FONT_HERSHEY_TRIPLEX,
        cv2.FONT_HERSHEY_COMPLEX_SMALL,
        cv2.FONT_HERSHEY_SCRIPT_SIMPLEX,
    ]
    for d in range(1, 10):
        for i in range(n_per_digit):
            side = int(rng.integers(28, 72))
            canvas = np.zeros((side, side), dtype=np.uint8)

            # Mix of backgrounds: 30% dark, 50% light, 20% mid-range
            r = rng.random()
            if r < 0.30:
                # Dark background, light text (UI / dark theme)
                bg = int(rng.integers(0, 60))
                col = int(rng.integers(180, 256))
            elif r < 0.80:
                # Light background, dark text (paper / printed)
                bg = int(rng.integers(190, 256))
                col = int(rng.integers(0, 70))
            else:
                # Mid-range
                bg = int(rng.integers(80, 160))
                col = int(rng.integers(0, 50)) if bg > 120 else int(rng.integers(200, 256))

            canvas[:] = bg
            fs = rng.uniform(0.7, 2.4)
            thick = int(rng.integers(1, 5))  # up to 4 thickness for bolder strokes
            font = fonts[int(rng.integers(0, len(fonts)))]
            t = str(d)
            (tw, th), _ = cv2.getTextSize(t, font, fs, thick)
            x0 = max(0, (side - tw) // 2 + int(rng.integers(-4, 5)))
            y0 = max(th + 2, (side + th) // 2 + int(rng.integers(-4, 5)))
            cv2.putText(canvas, t, (x0, y0), font, fs, col, thick, cv2.LINE_AA)
            canvas = _augment(canvas)

            # Normalize to white-on-black for feature consistency
            m = float(np.median(canvas))
            if m > 127:
                canvas = 255 - canvas

            feat = cv2.resize(canvas, (20, 20), interpolation=cv2.INTER_AREA).astype(np.float64).ravel() / 255.0
            X_list.append(feat)
            y_list.append(d)
    return np.asarray(X_list), np.asarray(y_list)


def _get_classifier():
    global _clf
    if _clf is not None:
        return _clf

    try:
        from sklearn.neural_network import MLPClassifier
        rng = np.random.default_rng(42)
        X, y = _build_training_data(rng)
        _clf = MLPClassifier(
            hidden_layer_sizes=(128, 64),
            max_iter=600,
            random_state=42,
            early_stopping=True,
            validation_fraction=0.15,
        )
        _clf.fit(X, y)
    except ImportError:
        # Fallback to LogisticRegression if MLP unavailable
        from sklearn.linear_model import LogisticRegression
        rng = np.random.default_rng(42)
        X, y = _build_training_data(rng)
        _clf = LogisticRegression(max_iter=3000, C=1.0, random_state=42)
        _clf.fit(X, y)

    return _clf


def _features_from_normalized(gray_u8: np.ndarray) -> np.ndarray:
    """20x20 float features from any uint8 ROI (caller normalises orientation)."""
    if gray_u8.size == 0:
        return np.zeros(20 * 20, dtype=np.float64)
    g = cv2.resize(gray_u8, (20, 20), interpolation=cv2.INTER_AREA)
    return g.astype(np.float64).ravel() / 255.0


def predict_digit_proba(gray_cell: np.ndarray) -> tuple[int, float]:
    """
    Predict digit from a grayscale cell ROI (full cell or tight crop).
    Returns (digit 1-9 or 0, max class probability).
    """
    if gray_cell is None or gray_cell.size == 0:
        return 0, 0.0
    clf = _get_classifier()
    x = _features_from_normalized(gray_cell).reshape(1, -1)
    proba = clf.predict_proba(x)[0]
    idx = int(np.argmax(proba))
    classes = clf.classes_
    digit = int(classes[idx])
    conf = float(proba[idx])
    return digit, conf


def predict_digit_top2(gray_cell: np.ndarray) -> tuple[tuple[int, float], tuple[int, float]]:
    """Best and second-best (digit, prob) for ambiguity resolution."""
    if gray_cell is None or gray_cell.size == 0:
        return (0, 0.0), (0, 0.0)
    clf = _get_classifier()
    x = _features_from_normalized(gray_cell).reshape(1, -1)
    proba = clf.predict_proba(x)[0]
    classes = clf.classes_.astype(int)
    order = np.argsort(proba)[::-1]
    i0, i1 = order[0], order[1] if len(order) > 1 else order[0]
    return (int(classes[i0]), float(proba[i0])), (int(classes[i1]), float(proba[i1]))


def predict_sudoku_digit(gray_cell: np.ndarray, min_confidence: float = 0.50) -> int:
    pred, conf = predict_digit_proba(gray_cell)
    if conf < min_confidence:
        return 0
    if 1 <= pred <= 9:
        return pred
    return 0
