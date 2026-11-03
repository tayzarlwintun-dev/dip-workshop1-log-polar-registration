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

## Step 2 – Log-polar transform (in progress)
**Goal:** turn each picture into its log-polar ("unrolled") form.
Rows = angle (0° to 360°), columns = log of the distance from the center.
**Expect:** rotating the photo makes the log-polar picture slide down;
zooming makes it slide right.

**Did:**

**Problems:**

**Results:**

**Limits:**
