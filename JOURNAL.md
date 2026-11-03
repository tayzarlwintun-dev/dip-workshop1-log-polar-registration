# Project Journal

## Step 0 – Setup (2026-11-04)
**Did:** made the project folder, a Python virtual environment (`.venv`),
installed opencv-python, numpy, matplotlib, scipy, started git, added a test photo.

**Photo:** `images/original.jpg` – Bangkok skyline, 418 × 625 pixels.
Lots of buildings and roads (good detail for matching). The top part is
mostly sky (smooth, little detail).

**Problems:** none. Added `.gitignore` so the big `.venv` folder is not saved in git.

**Next:** Step 1 – make test pictures with a known rotation, zoom and shift.

## Step 1 – Make test pictures (2026-11-04)
**Did:** wrote `step1_make_test_images.py`. It takes `original.jpg` and makes
4 changed copies where we know the true answer:

| Test | Rotation | Zoom | Shift (x, y) | Idea |
|---|---|---|---|---|
| test1 | 30° | ×1.0 | (0, 0) | rotation only |
| test2 | 0° | ×1.5 | (0, 0) | zoom only |
| test3 | 45° | ×1.5 | (20, −15) | all three |
| test4 | 135° | ×2.0 | (−25, 30) | hard case |
| test5 | 90° | ×1.2 | (10, 10) | my own test (added by me) |

Order of the change: rotate + zoom around the picture center, then shift.
Positive angle = counter-clockwise. True answers saved in `results/test_cases.json`.

**Problems:** the titles in the overview picture were cut off at the top.
Fixed with `bbox_inches="tight"` when saving.

**Results:** test1 has ~18% black corners (rotation pushes picture out of the frame).
Zoomed tests have no black, but lose the outer part of the scene
(test4 at ×2 keeps only the middle quarter).

**Limits:** the test pictures are made by the computer, so they are "perfect"
(no new noise, no lighting change). Real photos would be harder.

**Extra:** I added test5 myself (90°, ×1.2, shift (10, 10)). It ran fine.
At 90° the tall photo turns sideways, so black bars appear at the top and bottom.

**Next:** Step 2 – log-polar transform.

## Step 2 – Log-polar transform (2026-11-04)
**Goal:** turn each picture into its log-polar ("unrolled") form and check the
lecture idea: rotation = slide up/down, zoom = slide right.

**Did:** wrote `step2_log_polar.py`.
- Pictures are used in grayscale (only brightness is needed for matching).
- `cv2.warpPolar` with `WARP_POLAR_LOG`, centered on the picture center (209, 312).
- Size: 360 rows (1 row = 1°) × 256 columns (log distance). Max radius = 375.9 px
  (half the diagonal, so the corners are included).
- Check: slide the ORIGINAL's log-polar picture by the expected amount and compare
  it with each test's log-polar picture (average brightness difference, ignoring black).

**Results:**

| Test | Expected slide (rows, cols) | Difference before | After sliding | Verdict |
|---|---|---|---|---|
| test1 (30°) | (−30, 0) | 27.4 | **2.0** | match ✅ |
| test2 (×1.5) | (0, 17.5) | 24.9 | **6.5** | match ✅ |
| test3 (45°, ×1.5, shift) | (−45, 17.5) | 34.7 | 29.9 | no match (shifted) |
| test4 (135°, ×2, shift) | (−135, 29.9) | 59.9 | 42.7 | no match (shifted) |
| test5 (90°, ×1.2, shift) | (−90, 7.9) | 74.8 | 50.2 | no match (shifted) |

- Rotation really is a slide along the angle axis, and zoom really is a slide
  along the log-distance axis. The lecture idea is confirmed.
- Zoom ×1.5 → log(1.5) on OpenCV's log ruler = 17.5 columns.

**Problems / surprises:**
- Sign: a counter-clockwise turn gives a slide of **−30** rows (up), not +30.
  OpenCV's y-axis points down, so it measures angles clockwise. Same idea,
  opposite direction. Must remember this in Step 3.
- test3, test4 and test5 do not match. Not a bug: these pictures are also SHIFTED,
  so their center sits on a different part of the city and the unrolling starts
  from the wrong point. This is the translation problem from the paper → Step 4.

**Limits:**
- Black bumps on the right: the picture is a rectangle, so in some directions
  it ends before the max radius (like the baboon slide).
- Left side is blurry: near the center only a few pixels are stretched over many
  columns (log-polar gives the center too much space, the edges too little).
- Zoom: content pushed past the right edge is lost (no wrap-around), so the
  zoom match (6.5) is not as perfect as the rotation match (2.0).

**Next:** Step 3 – let the computer FIND the slide by itself (cross-correlation),
then turn it into rotation angle and zoom.

## Step 3 – Find rotation and zoom by itself (2026-11-04)
**Goal:** the computer finds the slide WITHOUT the answer key, then turns it
into rotation angle and zoom.

**Did:** wrote `step3_find_rotation_scale.py`.
- Unroll original and test picture (same as Step 2, center = middle of picture).
- Phase correlation: scores all 360 × 256 = 92,160 possible slides at once
  (Fourier transform), keeps the best one. Sub-pixel accuracy with a small
  parabola fit around the best spot. Hanning window softens the cut left/right edges.
- rows slid → angle = −rows / 360 × 360°;  columns slid → zoom = e^(cols × log(375.9) / 256)
- "Peak" = how strong the best match is (1 = perfect, ~0 = guessing).

**Results:**

| Test | True | Found | Angle error | Zoom error | Peak | Verdict |
|---|---|---|---|---|---|---|
| test1 | 30°, ×1.0 | 30.00°, ×1.000 | 0.00° | 0.00% | 0.850 | correct ✅ |
| test2 | 0°, ×1.5 | 0.00°, ×1.487 | 0.00° | 0.88% | 0.697 | correct ✅ |
| test3 | 45°, ×1.5 + shift | 46.15°, ×1.519 | 1.15° | 1.26% | 0.031 | weak, shifted |
| test4 | 135°, ×2.0 + shift | 137.34°, ×2.060 | 2.34° | 3.01% | 0.041 | weak, shifted |
| test5 | 90°, ×1.2 + shift | 88.02°, ×1.260 | 1.98° | 5.01% | 0.039 | weak, shifted |

**Problems / surprises:**
- The shifted tests are surprisingly CLOSE (1–2° off), because the shift is small
  (10–25 px). But the peak is ~20× weaker (0.03 vs 0.85), so the result is not reliable.
- Changed the verdict text from "wrong" to "not exact, weak peak" to be honest about this.

**Limits:**
- Center is always the middle of the picture → only works without shift.
- test2 peak (0.70) is lower than test1 (0.85): zoom pushes part of the picture
  off the right edge of the log-polar picture, so there is less to match.

**Questions I had:** see `QUESTIONS_AND_ANSWERS.md` (peak, what was manual in
Step 2, what Step 3 does, does it find the center).

**Next:** Step 4 – search for the right center to find the shift.
