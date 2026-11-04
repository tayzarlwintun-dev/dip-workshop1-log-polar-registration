"""
Step 7 - Hard tests: does my final method (version 2) also work on difficult photos?

Steps 1-6 use my 5 easy-to-medium test photos. Here are 8 HARDER ones:

  B0..B3 "friend-style" = like the paper's own example (Fig. 3), also used by my friend:
         turned 201 degrees clockwise, zoomed x2.13, a small stretch (the paper's numbers),
         a little camera noise. They differ in HOW FAR the photo was moved:
           B0  186 px  (the original's middle is NOT in the test photo)
           B1   50 px  (small move)
           B2  106 px  (big move)
           B3  100 px  (big move, the test photo's middle is in empty sky)
  C1..C4 extra tests: other turns and zooms (up to x3), big moves (90-192 px), no stretch.

How a hard test photo is made (different from Step 1):
  We choose which point of the original should become the MIDDLE of the test photo
  ("spot offset" from the original's middle). A big offset = a big move.

For each photo: Step 4 (search) -> Step 6 (optimizer), then measure "pixels off"
(same score as Steps 5 and 6). Under 0.1 px = practically perfect.

Output:
  images/generated/B0_friend_style.png ... C4_extra.png    the 8 hard test photos
  results/step7_hard_tests.json                            all numbers
  results/step7_hard_tests.png                             test photos + overlays
"""
import json
import os
import time

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import step4_find_shift as s4
import step6_optimizer as s6

OUT_DIR = "results"
PAPER_STRETCH = [[1.008, 0.006], [0.003, 1.045]]     # the paper's leftover stretch (Fig. 3)
NO_STRETCH = [[1.0, 0.0], [0.0, 1.0]]
GOOD = 0.1                                            # px: practically perfect

# name, turn (+ = counter-clockwise), zoom, spot offset (x, y), stretch, idea
HARD_TESTS = [
    ("B0", -201, 2.13, (110, -150), PAPER_STRETCH, "paper-style, original's middle NOT visible"),
    ("B1", -201, 2.13, (40, -30), PAPER_STRETCH, "paper-style, small move"),
    ("B2", -201, 2.13, (70, 80), PAPER_STRETCH, "paper-style, big move"),
    ("B3", -201, 2.13, (0, -100), PAPER_STRETCH, "paper-style, big move, middle in sky"),
    ("C1", 300, 3.0, (-90, 0), NO_STRETCH, "zoom x3, big move"),
    ("C2", 60, 1.3, (60, -90), NO_STRETCH, "big move"),
    ("C3", -120, 1.8, (-70, -90), NO_STRETCH, "big move"),
    ("C4", 10, 1.1, (120, 150), NO_STRETCH, "very big move"),
]


def make_hard_test(original, angle, zoom, spot_offset, stretch, seed=1):
    """The point `middle + spot_offset` of the original becomes the MIDDLE of the
    test photo, turned + zoomed + stretched. A little noise (like a camera).
    Returns the test photo and the TRUE matrix (original -> test)."""
    h, w = original.shape
    middle = np.array([w / 2, h / 2])
    turn_zoom = cv2.getRotationMatrix2D((0, 0), angle, zoom)[:, :2]
    L = np.array(stretch) @ turn_zoom
    spot = middle + np.array(spot_offset)
    m = np.hstack([L, (middle - L @ spot)[:, None]])
    test = cv2.warpAffine(original, m, (w, h), flags=cv2.INTER_CUBIC,
                          borderMode=cv2.BORDER_CONSTANT, borderValue=0)
    rng = np.random.default_rng(seed)
    test = np.where(test > 0, np.clip(test + rng.normal(0, 2.0, test.shape), 1, 255), 0)
    return test.astype(np.float32), m


def main():
    os.makedirs("images/generated", exist_ok=True)
    original = s4.load_gray("images/original.jpg")
    h, w = original.shape

    print(f"{'test':5} | {'turn':>5} {'zoom':>5} {'move':>5} | {'after search':>12} {'after optimizer':>15} | "
          f"{'time':>6} | verdict")
    print("-" * 78)
    results, rows = [], []
    for name, angle, zoom, offset, stretch, idea in HARD_TESTS:
        test, m_true = make_hard_test(original, angle, zoom, offset, stretch)
        fname = f"images/generated/{name}_friend_style.png" if name[0] == "B" \
            else f"images/generated/{name}_extra.png"
        cv2.imwrite(fname, test.astype(np.uint8))

        start = time.time()
        r = s4.find_turn_zoom_shift(original, test)                       # Step 4
        m4 = s6.make_matrix(w, h, r["angle"], r["scale"], r["shift"][0], r["shift"][1])
        m6, _ = s6.optimize(original, test, m4)                           # Step 6
        secs = time.time() - start

        off4 = s6.pixels_off(m4, m_true, test)
        off6 = s6.pixels_off(m6, m_true, test)
        move = float(np.hypot(*offset))
        ok = off6 < GOOD
        print(f"{name:5} | {angle:5} {zoom:5.2f} {move:5.0f} | {off4:10.2f}px {off6:13.3f}px | "
              f"{secs:5.1f}s | {'PERFECT' if ok else 'NOT EXACT'}")
        results.append({"name": name, "idea": idea, "turn": angle, "zoom": zoom,
                        "spot_offset": list(offset), "move_px": round(move, 1),
                        "stretch": stretch,
                        "pixels_off_after_search": round(off4, 3),
                        "pixels_off_after_optimizer": round(off6, 4),
                        "seconds": round(secs, 2), "practically_perfect": bool(ok)})
        rows.append((name, idea, test, m6, off6))

    with open(os.path.join(OUT_DIR, "step7_hard_tests.json"), "w") as f:
        json.dump(results, f, indent=2)
    good = sum(r["practically_perfect"] for r in results)
    print(f"\nPractically perfect (< {GOOD} px): {good} / {len(results)}")
    print("Saved results/step7_hard_tests.json")

    # ---- Figure: test photo (top) and overlay after alignment (bottom) ----
    fig, axes = plt.subplots(2, len(rows), figsize=(2.3 * len(rows), 7.2))
    o8 = original.astype(np.uint8)
    for i, (name, idea, test, m6, off6) in enumerate(rows):
        axes[0, i].imshow(test, cmap="gray", vmin=0, vmax=255)
        axes[0, i].set_title(f"{name}\n{idea}", fontsize=7.5)
        fixed = s6.undo(test, m6, w, h).astype(np.uint8)
        axes[1, i].imshow(np.dstack([o8, fixed, fixed]))
        axes[1, i].set_title(f"put back: {off6:.3f} px off", fontsize=8.5)
        for a in axes[:, i]:
            a.axis("off")
    fig.suptitle("Step 7: hard test photos (top) and put back on the original (bottom)\n"
                 "red = original only, gray = lined up", fontsize=11)
    plt.tight_layout(h_pad=2.5)
    plt.savefig(os.path.join(OUT_DIR, "step7_hard_tests.png"), dpi=110, bbox_inches="tight")
    plt.close()
    print("Saved results/step7_hard_tests.png")


if __name__ == "__main__":
    main()
