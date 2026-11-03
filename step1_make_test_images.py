"""
Step 1 - Make test pictures with a KNOWN rotation, zoom and shift.

Why: to check if our registration program works, we need pictures where
we already know the correct answer. So we take one photo and turn, zoom
and move it ourselves. Later steps must find these numbers on their own.

How the change is made (same order for every test):
  1. rotate by ANGLE degrees around the picture center
     (positive = counter-clockwise, like in math class)
  2. zoom by SCALE around the picture center (2.0 = twice as big)
  3. shift by (SHIFT_X, SHIFT_Y) pixels (+x = right, +y = down)

Output:
  images/generated/testN.png      the changed pictures
  results/test_cases.json          the true answers
  results/step1_test_images.png    all pictures side by side
"""

import json
import os

import cv2
import matplotlib.pyplot as plt
import numpy as np

# ---------------------------------------------------------------
# Settings - the test cases (you can change or add your own)
# ---------------------------------------------------------------
TEST_CASES = [
    {"name": "test1", "angle": 30, "scale": 1.0, "shift_x": 0, "shift_y": 0,
     "note": "rotation only"},
    {"name": "test2", "angle": 0, "scale": 1.5, "shift_x": 0, "shift_y": 0,
     "note": "zoom only"},
    {"name": "test3", "angle": 45, "scale": 1.5, "shift_x": 20, "shift_y": -15,
     "note": "rotation + zoom + shift"},
    {"name": "test4", "angle": 135, "scale": 2.0, "shift_x": -25, "shift_y": 30,
     "note": "hard: big rotation + big zoom + shift"},
     {"name": "test5", "angle": 90, "scale": 1.2, "shift_x": 10, "shift_y": 10, "note": "my test"},
]

ORIGINAL_PATH = "images/original.jpg"
OUT_IMAGE_DIR = "images/generated"
OUT_RESULTS_DIR = "results"


def make_transform_matrix(width, height, angle, scale, shift_x, shift_y):
    """Build the 2x3 matrix that rotates + zooms around the center, then shifts."""
    center = (width / 2, height / 2)
    # OpenCV builds "rotate + zoom around the center" for us
    matrix = cv2.getRotationMatrix2D(center, angle, scale)
    # the last column of the matrix is the shift, so we just add ours
    matrix[0, 2] += shift_x
    matrix[1, 2] += shift_y
    return matrix


def apply_transform(image, matrix):
    """Move every pixel using the matrix. Empty areas become black."""
    height, width = image.shape[:2]
    return cv2.warpAffine(image, matrix, (width, height),
                          flags=cv2.INTER_LINEAR,
                          borderMode=cv2.BORDER_CONSTANT, borderValue=0)


def main():
    os.makedirs(OUT_IMAGE_DIR, exist_ok=True)
    os.makedirs(OUT_RESULTS_DIR, exist_ok=True)

    # 1) load the photo
    original = cv2.imread(ORIGINAL_PATH)
    if original is None:
        raise FileNotFoundError(f"Could not open {ORIGINAL_PATH}")
    height, width = original.shape[:2]
    print(f"Original photo: {width} x {height} pixels")

    # 2) make each test picture
    results = []
    for case in TEST_CASES:
        matrix = make_transform_matrix(width, height, case["angle"], case["scale"],
                                       case["shift_x"], case["shift_y"])
        changed = apply_transform(original, matrix)
        out_path = os.path.join(OUT_IMAGE_DIR, case["name"] + ".png")
        cv2.imwrite(out_path, changed)

        # how much of the picture is black (empty) after the change
        black = np.all(changed == 0, axis=2).mean() * 100
        print(f"{case['name']}: angle={case['angle']:>4} deg  scale={case['scale']:.2f}  "
              f"shift=({case['shift_x']:>4},{case['shift_y']:>4})  "
              f"black area={black:4.1f}%  -> {out_path}")

        results.append({**case, "file": out_path,
                        "matrix": matrix.round(6).tolist()})

    # 3) save the true answers
    truth_path = os.path.join(OUT_RESULTS_DIR, "test_cases.json")
    with open(truth_path, "w") as f:
        json.dump({"original": ORIGINAL_PATH, "width": width, "height": height,
                   "tests": results}, f, indent=2)
    print(f"True answers saved to {truth_path}")

    # 4) show everything side by side
    n = len(results) + 1
    fig, axes = plt.subplots(1, n, figsize=(3.2 * n, 5))
    axes[0].imshow(cv2.cvtColor(original, cv2.COLOR_BGR2RGB))
    axes[0].set_title("original")
    for ax, case in zip(axes[1:], results):
        img = cv2.imread(case["file"])
        ax.imshow(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
        ax.set_title(f"{case['name']}\n{case['angle']} deg, x{case['scale']}, "
                     f"shift ({case['shift_x']},{case['shift_y']})", fontsize=9)
    for ax in axes:
        ax.axis("off")
    plt.tight_layout()
    fig_path = os.path.join(OUT_RESULTS_DIR, "step1_test_images.png")
    plt.savefig(fig_path, dpi=120, bbox_inches="tight")
    print(f"Overview picture saved to {fig_path}")


if __name__ == "__main__":
    main()
