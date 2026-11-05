"""
Picture that explains Step 4 with test4: where is "the middle", where are the 12 short-listed
places, where is the cyan circle, and how the move comes out.
Run from the main folder:  python explanations/make_step4_explained.py
Output: explanations/step4_explained.png
"""
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
os.chdir(ROOT)
sys.path.insert(0, ROOT)
import step4_find_shift as s4


def main():
    o = s4.load_gray("images/original.jpg")
    t = s4.load_gray("images/generated/test4.png")
    h, w = o.shape
    mid = (w / 2, h / 2)
    O = s4.add_gray_frame(o, np.ones(o.shape, bool))
    T = s4.add_gray_frame(t, t > 0)
    r = s4.search_from_anchor(O, T, mid, (h, w))
    sx, sy = r["spot"]

    fig, ax = plt.subplots(1, 2, figsize=(13, 9.5))
    ax[0].imshow(t, cmap="gray")
    ax[0].plot(*mid, "o", color="#e34948", ms=14, mec="white", mew=2)
    ax[0].set_title("TEST photo (test4)\nred dot = its MIDDLE: we keep this fixed\n"
                    "and ask: where is this building in the original?", fontsize=11)
    ax[1].imshow(o, cmap="gray")
    for i, (cx, cy) in enumerate(r["candidates"]):
        ax[1].plot(cx, cy, "o", color="#eda100", ms=7, mec="black", mew=0.8,
                   label="the 12 short-listed places" if i == 0 else None)
    ax[1].plot(*mid, "P", color="white", ms=14, mec="black", mew=1.5, label="middle of the ORIGINAL (209, 312)")
    ax[1].plot(sx, sy, "o", mfc="none", mec="#00d0ff", ms=22, mew=3,
               label=f"cyan circle = best place ({sx:.0f}, {sy:.0f})")
    ax[1].annotate("", xy=(sx, sy), xytext=mid, arrowprops=dict(arrowstyle="-|>", color="#00d0ff", lw=2.5))
    ax[1].set_title("ORIGINAL photo: the search happens HERE\n"
                    f"the circle is {sy - mid[1]:.0f} px below the original's middle\n"
                    "→ turned 135° and zoomed ×2 = move (−24, 30)  (true: −25, 30)", fontsize=11)
    ax[1].legend(loc="upper center", bbox_to_anchor=(0.5, -0.02), fontsize=10, frameon=False, ncol=1)
    for a in ax:
        a.set_xticks([])
        a.set_yticks([])
    fig.suptitle("Step 4: find the TEST photo's middle inside the ORIGINAL photo", fontsize=14, fontweight="bold")
    plt.tight_layout(rect=(0, 0, 1, 0.95))
    out = os.path.join(HERE, "step4_explained.png")
    plt.savefig(out, dpi=90, bbox_inches="tight")
    print("Saved", out, "candidates:", [(round(a), round(b)) for a, b in r["candidates"]], "spot", r["spot"])


if __name__ == "__main__":
    main()
