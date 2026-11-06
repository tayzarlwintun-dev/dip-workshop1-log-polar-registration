"""
Simplest picture for "why blur?": one thin line in each photo.
Red = original line, cyan = test line (10 px to the right). Gray/white = overlap.
Run from the main folder:  python explanations/make_blur_simple.py  -> explanations/blur_simple.png
"""
import os
import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 120, 70


def line(x, blur):
    img = np.zeros((H, W), np.float32)
    img[:, x - 1:x + 1] = 255
    return cv2.GaussianBlur(img, (0, 0), blur) if blur > 0 else img


def diff(a, b):
    return float(np.mean((a - b) ** 2))


def overlay(a, b):
    a8 = np.clip(a / a.max() * 255, 0, 255).astype(np.uint8)
    b8 = np.clip(b / b.max() * 255, 0, 255).astype(np.uint8)
    return np.dstack([a8, b8, b8])


def main():
    fig, ax = plt.subplots(1, 3, figsize=(16, 5))
    cases = [(0, "SHARP lines", "no overlap at all"), (6, "BLURRY lines (blur 6)", "they overlap"),
             (0, "SHARP again, now close", "")]
    for k, (blur, name, _) in enumerate(cases):
        x_test = 70 if k < 2 else 61
        o, t = line(60, blur), line(x_test, blur)
        now = diff(o, t)
        closer = diff(o, line(x_test - 1, blur))     # test moved 1 px toward the original
        away = diff(o, line(x_test + 1, blur))       # test moved 1 px away
        ax[k].imshow(overlay(o, t), interpolation="nearest")
        ax[k].set_xticks([])
        ax[k].set_yticks([])
        if k == 0:
            verdict = "SAME score both ways\n→ it doesn't know which way to go → STUCK"
        elif k == 1:
            verdict = "move closer = BETTER, away = WORSE\n→ it knows the way → moves left"
        else:
            verdict = "now close: sharp lines give\nthe EXACT position"
        ax[k].set_title(f"{k + 1}. {name}\nred = original, cyan = test ({x_test - 60} px apart)", fontsize=11)
        ax[k].set_xlabel(f"difference now: {now:.0f}\n"
                         f"test moved 1 px CLOSER: {closer:.0f}    1 px AWAY: {away:.0f}\n\n{verdict}",
                         fontsize=10.5)
    fig.suptitle("Why blur? The optimizer only checks: \"if I move 1 pixel, does the difference get smaller?\"",
                 fontsize=13, fontweight="bold")
    plt.tight_layout(rect=(0, 0, 1, 0.92))
    out = os.path.join(HERE, "blur_simple.png")
    plt.savefig(out, dpi=100, bbox_inches="tight")
    print("Saved", out)


if __name__ == "__main__":
    main()
