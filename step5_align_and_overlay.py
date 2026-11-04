"""
Step 5 - Put each test photo BACK on top of the original, and show they line up.

Simple idea:
  Step 4 told us how each test photo was changed (turn, zoom, shift).
  Now we do the OPPOSITE: un-shift, un-zoom, un-turn the test photo.
  If our numbers are right, it lands exactly on top of the original.

How we show it (color overlay):
  - original photo  -> drawn in RED
  - fixed test photo -> drawn in GREEN + BLUE (cyan)
  - where they line up, red + cyan = GRAY (looks normal)
  - where they do NOT line up, you see RED and CYAN edges ("double picture")

We also measure:
  - difference BEFORE fixing   (test photo straight on top of the original)
  - difference AFTER fixing     (with our Step 4 numbers)
  - difference with the TRUE numbers (best possible)
  - "pixels off": on average, how far each pixel lands from where it should be

Output:
  images/aligned/testN_aligned.png   the fixed test photos
  results/step5_overlay.png          before / after color overlays
  results/step5_results.json         the numbers
"""

import json
import os

import cv2
import matplotlib.pyplot as plt
import numpy as np

TRUTH_PATH = "results/test_cases.json"
FOUND_PATH = "results/step4_results.json"
OUT_IMAGE_DIR = "images/aligned"
OUT_DIR = "results"


def make_matrix(width, height, angle, scale, shift_x, shift_y):
    """The same recipe as Step 1: turn + zoom around the middle, then shift.
    (original -> test photo)"""
    m = cv2.getRotationMatrix2D((width / 2, height / 2), angle, scale)
    m[0, 2] += shift_x
    m[1, 2] += shift_y
    return m


def undo(test_img, matrix, width, height):
    """Do the recipe BACKWARDS: test photo -> original position.
    WARP_INVERSE_MAP tells OpenCV to use the opposite of the matrix."""
    return cv2.warpAffine(test_img, matrix, (width, height),
                          flags=cv2.INTER_LINEAR | cv2.WARP_INVERSE_MAP,
                          borderMode=cv2.BORDER_CONSTANT, borderValue=0)


def coverage_mask(matrix, width, height):
    """Which pixels of the fixed photo really came from the test photo
    (and are not black empty area)."""
    ones = np.full((height, width), 255, np.uint8)
    back = cv2.warpAffine(ones, matrix, (width, height),
                          flags=cv2.INTER_NEAREST | cv2.WARP_INVERSE_MAP,
                          borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    return back > 0


def difference(a, b, mask):
    """Average brightness difference (0 = identical) inside the mask."""
    return float(np.abs(a.astype(np.float32) - b.astype(np.float32))[mask].mean())


def pixels_off(m_found, m_true, visible):
    """On average, how many pixels apart each VISIBLE point of the fixed photo is
    from where it should be (measured in original-photo pixels).
    We only use pixels the test photo really shows (zoomed photos show only the middle)."""
    inv_found = cv2.invertAffineTransform(m_found)
    inv_true = cv2.invertAffineTransform(m_true)
    ys, xs = np.nonzero(visible)
    pts = np.stack([xs, ys, np.ones(xs.size)]).astype(np.float64)
    return float(np.linalg.norm(inv_found @ pts - inv_true @ pts, axis=0).mean())


def color_overlay(original_gray, other_gray):
    """Red = original, cyan = other. Same picture -> gray."""
    return np.dstack([original_gray, other_gray, other_gray])


def main():
    os.makedirs(OUT_IMAGE_DIR, exist_ok=True)
    with open(TRUTH_PATH) as f:
        truth = json.load(f)
    with open(FOUND_PATH) as f:
        found = {r["name"]: r for r in json.load(f)}

    original = cv2.imread(truth["original"], cv2.IMREAD_GRAYSCALE)
    h, w = original.shape

    print(f"{'test':6} {'before':>8} {'after (ours)':>13} {'after (true)':>13} {'pixels off':>11} | verdict")
    print("-" * 70)

    rows, results = [], []
    for t in truth["tests"]:
        f = found[t["name"]]
        test = cv2.imread(t["file"], cv2.IMREAD_GRAYSCALE)

        m_found = make_matrix(w, h, f["angle_found"], f["scale_found"], *f["shift_found"])
        m_true = make_matrix(w, h, t["angle"], t["scale"], t["shift_x"], t["shift_y"])

        fixed = undo(test, m_found, w, h)
        fixed_true = undo(test, m_true, w, h)
        cv2.imwrite(os.path.join(OUT_IMAGE_DIR, f"{t['name']}_aligned.png"), fixed)

        # only compare where the test photo really has picture (not black empty area)
        mask = coverage_mask(m_found, w, h) & coverage_mask(m_true, w, h)
        mask_before = test > 0

        d_before = difference(original, test, mask_before)
        d_after = difference(original, fixed, mask)
        d_true = difference(original, fixed_true, mask)
        off = pixels_off(m_found, m_true, mask_before)
        ok = off < 3.0

        print(f"{t['name']:6} {d_before:8.1f} {d_after:13.1f} {d_true:13.1f} {off:9.2f}px | "
              f"{'LINED UP' if ok else 'NOT lined up'}")

        results.append({"name": t["name"], "difference_before": round(d_before, 2),
                        "difference_after_ours": round(d_after, 2),
                        "difference_after_true": round(d_true, 2),
                        "pixels_off": round(off, 2), "lined_up": bool(ok)})
        rows.append((t, test, fixed, d_before, d_after, off))

    with open(os.path.join(OUT_DIR, "step5_results.json"), "w") as fp:
        json.dump(results, fp, indent=2)
    print("\nSaved results/step5_results.json")

    # ---- Figure: one row per test ----
    n = len(rows)
    fig, axes = plt.subplots(n, 4, figsize=(11, 3.6 * n))
    for r, (t, test, fixed, d_before, d_after, off) in enumerate(rows):
        axes[r, 0].imshow(test, cmap="gray")
        axes[r, 0].set_title(f"{t['name']}: test photo\n({t['angle']} deg, x{t['scale']}, "
                             f"shift {t['shift_x']},{t['shift_y']})", fontsize=9)
        axes[r, 1].imshow(color_overlay(original, test))
        axes[r, 1].set_title(f"BEFORE: test on top of original\ndifference {d_before:.1f}", fontsize=9)
        axes[r, 2].imshow(fixed, cmap="gray")
        axes[r, 2].set_title("test photo FIXED\n(un-turn, un-zoom, un-shift)", fontsize=9)
        axes[r, 3].imshow(color_overlay(original, fixed))
        axes[r, 3].set_title(f"AFTER: fixed on top of original\ndifference {d_after:.1f}, "
                             f"{off:.1f} px off", fontsize=9)
        for ax in axes[r]:
            ax.axis("off")
    fig.suptitle("Red = original, cyan = test.  Gray = lined up.  Red/cyan edges = NOT lined up.\n"
                 "Plain red = part of the original that the test photo does not show.",
                 fontsize=12, y=1.01)
    plt.tight_layout()
    out = os.path.join(OUT_DIR, "step5_overlay.png")
    plt.savefig(out, dpi=90, bbox_inches="tight")
    plt.close()
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
