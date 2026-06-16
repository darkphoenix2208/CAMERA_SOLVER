import requests
import json
import sys

url = "http://localhost:8000/solve"

# A solved cube with a single 'U' move applied
# True solved state: U=W, R=R, F=G, D=Y, L=O, B=B
# 
# Applying U (clockwise):
# U face stays all W.
# R face top row gets B face top row -> 'B' (Blue)
# F face top row gets R face top row -> 'R' (Red)
# L face top row gets F face top row -> 'G' (Green)
# B face top row gets L face top row -> 'O' (Orange)
# D face is unaffected.

payload = {
    "faces": {
        "U": ["W", "W", "W", "W", "W", "W", "W", "W", "W"],
        "R": ["B", "B", "B", "R", "R", "R", "R", "R", "R"],
        "F": ["R", "R", "R", "G", "G", "G", "G", "G", "G"],
        "D": ["Y", "Y", "Y", "Y", "Y", "Y", "Y", "Y", "Y"],
        "L": ["G", "G", "G", "O", "O", "O", "O", "O", "O"],
        "B": ["O", "O", "O", "B", "B", "B", "B", "B", "B"]
    }
}

try:
    print("Testing Cube Solver API with 1-move scrambled state...")
    resp = requests.post(url, json=payload)
    data = resp.json()

    print("Response Status Code:", resp.status_code)
    print("Response JSON:")
    print(json.dumps(data, indent=2))
    
    if data.get("success"):
        print("\n✅ Cube Solver is fully functional!")
        print(f"Solution steps: {' '.join(data.get('solution', []))}")
    else:
        print("\n❌ Cube Solver returned an error.")
        
except Exception as e:
    print("\n❌ Request failed:", e)
    sys.exit(1)
