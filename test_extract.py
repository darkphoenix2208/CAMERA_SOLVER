"""Quick test: POST the sudoku image to the backend and print the extracted grid."""
import requests
import sys
import os

IMAGE_PATH = sys.argv[1] if len(sys.argv) > 1 else None

if IMAGE_PATH is None or not os.path.isfile(IMAGE_PATH):
    print("Usage: python test_extract.py <image_path>")
    sys.exit(1)

url = "http://localhost:8000/extract-sudoku"

with open(IMAGE_PATH, "rb") as f:
    resp = requests.post(url, files={"file": ("sudoku.png", f, "image/png")})

data = resp.json()
if not data.get("success"):
    print("FAILED:", data.get("error"))
    sys.exit(1)

print("Extracted board:")
for row in data["board"]:
    print([str(x) if x else "." for x in row])

# Ground truth for the puzzle in the user's image
ground_truth = [
    [0, 0, 0, 0, 0, 0, 0, 0, 8],
    [0, 1, 8, 0, 0, 0, 9, 5, 0],
    [6, 4, 9, 0, 0, 0, 0, 0, 0],
    [2, 8, 0, 0, 0, 1, 0, 9, 3],
    [0, 0, 6, 8, 9, 2, 1, 0, 0],
    [9, 0, 0, 7, 0, 0, 0, 2, 6],
    [0, 9, 0, 0, 3, 0, 6, 0, 7],
    [0, 0, 0, 0, 0, 7, 5, 0, 1],
    [0, 0, 4, 6, 5, 0, 0, 0, 0],
]

correct = 0
total = 81
for r in range(9):
    for c in range(9):
        if data["board"][r][c] == ground_truth[r][c]:
            correct += 1

print(f"\nAccuracy: {correct}/81 = {correct/81*100:.1f}%")

# Show mismatches
mismatches = []
for r in range(9):
    for c in range(9):
        got = data["board"][r][c]
        want = ground_truth[r][c]
        if got != want:
            mismatches.append(f"  ({r},{c}): got {got}, want {want}")
if mismatches:
    print(f"\nMismatches ({len(mismatches)}):")
    for m in mismatches:
        print(m)
else:
    print("\nPerfect extraction!")
