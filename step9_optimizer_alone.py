"""
Step 9 - The paper's main point: the optimizer ALONE gets lost.

The paper says: the Levenberg-Marquardt optimizer (Step 6) only works if it STARTS CLOSE
to the right answer. That's why the log-polar search (Step 4) must come first.

Here we test it on my 5 test photos, two ways:
  A. Optimizer ALONE:          start from "no change" (no turn, no zoom, no move)
  B. Log-polar + optimizer:    start from Step 4's answer (my normal method)

Example: walking downhill blindfolded. If you start near the right valley (B), you reach
its bottom. If you start somewhere random (A), you walk into the WRONG valley and stop there.

Output:
  results/step9_optimizer_alone.json
  results/step9_optimizer_alone.png   (top row = A, bottom row = B; gray = lined up)
"""
import json
import os
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import step4_find_shift as s4
import step6_optimizer as s6

TRUTH_PATH = "results/test_cases.json"
OUT_DIR = "results"
NO_CHANGE = np.array([[1.0, 0.0, 0.0],
                      [0.0, 1.0, 0.0]])     # "no turn, no zoom, no move"
LOST = 2.0                                  # px: more than this = the optimizer got lost


def overlay(original, test, m, w, h):
    """Red = original, cyan = test photo put back. Gray = lined up."""
    back = s6.undo(test, m, w, h).astype(np.uint8)
    return np.dstack([original.astype(np.uint8), back, back])


def main():
    with open(TRUTH_PATH) as f:
        truth = json.load(f)
    original = s4.load_gray(truth["original"])
    h, w = original.shape

    print(f"{'test':6} | {'A: optimizer ALONE':>24} | {'B: log-polar + optimizer':>26}")
    print("-" * 64)
    results, pictures = [], []
    for t in truth["tests"]:
        test = s4.load_gray(t["file"])
        m_true = np.array(t["matrix"])

        # A. optimizer alone, starting from "no change"
        start = time.time()
        m_alone, _ = s6.optimize(original, test, NO_CHANGE)
        t_alone = time.time() - start
        off_alone = s6.pixels_off(m_alone, m_true, test)

        # B. my normal method: Step 4 first, then the optimizer
        start = time.time()
        r = s4.find_turn_zoom_shift(original, test)
        m4 = s6.make_matrix(w, h, r["angle"], r["scale"], r["shift"][0], r["shift"][1])
        m_both, _ = s6.optimize(original, test, m4)
        t_both = time.time() - start
        off_both = s6.pixels_off(m_both, m_true, test)

        a_word = "LOST" if off_alone > LOST else "ok"
        b_word = "LOST" if off_both > LOST else "ok"
        print(f"{t['name']:6} | {off_alone:12.2f} px off  {a_word:4} | {off_both:14.3f} px off  {b_word:4}")
        results.append({"name": t["name"], "turn": t["angle"], "zoom": t["scale"],
                        "move": [t["shift_x"], t["shift_y"]],
                        "optimizer_alone_pixels_off": round(off_alone, 2),
                        "optimizer_alone_seconds": round(t_alone, 1),
                        "logpolar_plus_optimizer_pixels_off": round(off_both, 4),
                        "logpolar_plus_optimizer_seconds": round(t_both, 1)})
        pictures.append((t, test, m_alone, off_alone, m_both, off_both))

    with open(os.path.join(OUT_DIR, "step9_optimizer_alone.json"), "w") as f:
        json.dump(results, f, indent=2)
    lost = sum(r["optimizer_alone_pixels_off"] > LOST for r in results)
    print(f"\nOptimizer ALONE got lost on {lost} of {len(results)} tests.")
    print("Saved results/step9_optimizer_alone.json")

    # ---- Picture: top = optimizer alone, bottom = log-polar + optimizer ----
    fig, ax = plt.subplots(2, len(pictures), figsize=(3.2 * len(pictures), 10.5))
    for i, (t, test, m_alone, off_alone, m_both, off_both) in enumerate(pictures):
        ax[0, i].imshow(overlay(original, test, m_alone, w, h))
        ax[0, i].set_title(f"{t['name']} (turn {t['angle']}°, zoom ×{t['scale']})\n"
                           f"optimizer ALONE: {off_alone:.1f} px off", fontsize=9.5)
        ax[1, i].imshow(overlay(original, test, m_both, w, h))
        ax[1, i].set_title(f"log-polar + optimizer:\n{off_both:.3f} px off", fontsize=9.5)
        for a in ax[:, i]:
            a.axis("off")
    fig.text(0.005, 0.73, "A. optimizer ALONE\n(start: no change)", fontsize=12, fontweight="bold",
             rotation=90, va="center")
    fig.text(0.005, 0.27, "B. log-polar first\n(start: Step 4)", fontsize=12, fontweight="bold",
             rotation=90, va="center")
    fig.suptitle("The optimizer only works if it starts close: red = original, cyan = test put back, "
                 "gray = lined up", fontsize=12, fontweight="bold")
    plt.tight_layout(rect=(0.03, 0, 1, 0.95), h_pad=2.5)
    plt.savefig(os.path.join(OUT_DIR, "step9_optimizer_alone.png"), dpi=100, bbox_inches="tight")
    plt.close()
    print("Saved results/step9_optimizer_alone.png")


if __name__ == "__main__":
    main()
