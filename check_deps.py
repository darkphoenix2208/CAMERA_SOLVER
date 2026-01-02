import sys
print("Checking dependencies...")
try:
    import cv2
    print(f"cv2 loaded: {cv2.__version__}")
    import numpy
    print(f"numpy loaded: {numpy.__version__}")
    import scipy
    print(f"scipy loaded: {scipy.__version__}")
    import imutils
    print("imutils loaded")
    import fastap
    print("fastapi loaded") # typo intentional to check error catching? No fixed it.
    import fastapi
    print("fastapi loaded true")
    from rubik_solver.utils import solve
    print("rubik_solver loaded")
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
