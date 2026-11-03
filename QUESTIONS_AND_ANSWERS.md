# Questions and Answers

My own questions while doing the workshop, with simple answers.

---

## Q1. In Step 2, what did we do "manually"?

We did NOT let the computer find anything. **We already knew the answer**
(from `results/test_cases.json`), so we told the program exactly how far to slide.

What the program did, step by step:
1. Unroll the original picture (log-polar).
2. Unroll test1 (log-polar).
3. **We calculated** how far it should slide, using the known answer:
   - test1 is rotated 30°  → 30 / 360 × 360 rows = **30 rows** (−30 = up, because of OpenCV's y-axis)
   - test2 is zoomed ×1.5   → log(1.5) on the log ruler = **17.5 columns** right
4. Slide the original's unrolled picture by that amount.
5. Compare it with test1's unrolled picture → difference 27.4 → **2.0** (almost the same).

So Step 2 only **proved the idea** ("rotation = slide, zoom = slide").
It is like checking a math answer when you already have the answer key.

---

## Q2. In Step 3, what does the computer do by itself?

Now the program does **NOT** get the answer. It must find the slide itself.

1. Unroll the original and the test picture (same as Step 2).
2. **Try every possible slide** – every number of rows up/down (360 options)
   × every number of columns left/right (256 options) = **92,160 slides**.
3. For each slide, give a **score**: how well the two unrolled pictures match.
4. Keep the slide with the **highest score**.
5. Turn it into answers:
   - rows slid  → rotation angle  (−30 rows → 30°)
   - columns slid → zoom           (17.1 columns → ×1.49)

Scoring 92,160 slides one by one is slow, so we use **phase correlation**:
a math trick (Fourier transform) that scores **all slides at once**.
The answer is the same as trying them one by one, just much faster.

---

## Q3. Does Step 3 find the CENTER of the picture?

**No.** Step 3 does **not** search for the center.
It always unrolls both pictures around the **middle of the picture** (209, 312).

- This is fine for test1 and test2, because they were only rotated / zoomed
  **around the middle**, so the middle is still the same spot of the city.
- For test3, test4 and test5 the picture was also **shifted**, so the middle
  of the test picture is now a **different spot of the city**.
  Both pictures get unrolled around different spots → they don't match well.

**Finding the right center is Step 4.**

---

## Q4. What is the "peak"?

The **peak = the highest score** in the score map = how strongly the best
slide matches. It tells us **how sure** the program is.

Small 1-D example (one row of pixels):
```
Picture 1:  0 0 5 9 5 0 0 0
Picture 2:  0 0 0 0 5 9 5 0
```
| Slide | Score |
|---|---|
| 0 | 25 |
| 1 | 90 |
| 2 | **131** ← highest = the peak |
| 3 | 90 |

The best slide is 2, and the peak value is 131.

In phase correlation, scores are scaled so that:
- **peak = 1.0** → the two pictures are exactly the same after sliding (perfect)
- **peak ≈ 0** → nothing matches, the "best" slide is basically a guess

Our results:
| Test | Peak | Meaning |
|---|---|---|
| test1 | 0.85 | very sure (clean map, one bright dot) |
| test2 | 0.70 | sure (a bit lower: zoom pushed some picture off the edge) |
| test3–5 | 0.03–0.04 | very unsure (noisy map, faint dot) – picture is shifted |

In `results/step3_peaks.png`, the peak is the **bright dot inside the circle**.

---

## Q5. "Off by 1–2" – off by what? The center?

**No, not the center.** It is the error in the **rotation angle**, in **degrees**.

| Test | True angle | Found angle | Error |
|---|---|---|---|
| test3 | 45° | 46.15° | 1.15° |
| test4 | 135° | 137.34° | 2.34° |
| test5 | 90° | 88.02° | 1.98° |

The zoom also has an error (in **percent**): test5 found ×1.26 instead of ×1.20 → 5% off.

Why is it close but not exact? The shift is small (10–25 pixels), so the two
centers are only a little apart → the unrolled pictures still look a bit alike.
But the match is weak (low peak), so the answer is not exact and not reliable.
With a bigger shift it could be completely wrong.

---

## Q6. Summary of Steps 2, 3, 4

| Step | Center used | Slide | Who knows the answer? |
|---|---|---|---|
| 2 | middle of picture | **we calculate it** from the answer key | we do (check only) |
| 3 | middle of picture | **computer finds it** (phase correlation) | computer finds rotation + zoom |
| 4 | **computer searches** many centers | computer finds it for each center | computer finds rotation + zoom + shift |

---

## Q7. Simple summary of Steps 1–3 (example: test1, photo turned 30°)

**Big goal:** photo 2 is turned, zoomed and moved. The computer must tell us how much.

**Step 1 – make a puzzle with an answer key.**
We turned the photo 30° ourselves (test1) and wrote the answer in `test_cases.json`.
Like a teacher writing a test AND the answer sheet.

**Step 2 – unroll and check the idea (using the answer key).**
1. Unroll the original (log-polar) – like peeling a can label flat.
2. Unroll test1.
3. They look the same, just one is moved up.
4. WE calculate from the answer key: 30° = move up 30 rows.
5. Move the original's flat picture up 30 rows and compare → difference 2.0 (almost identical).
→ Turning = flat picture moves up/down. Zooming = flat picture moves right.
→ The computer found NOTHING here. We gave it the answer. We only proved the idea.
Like a teacher checking that the answer sheet is correct.

**Step 3 – the computer finds it by itself (no answer key).**
1. Put flat picture 2 on top of flat picture 1 (like two transparent sheets).
2. Try every position (92,160 of them), give each a score.
3. Keep the best one (the peak): "up 30 rows, right 0 columns".
4. Convert: 30 rows → turned 30°, 0 columns → zoom ×1.0.
5. Grade with the answer key → exactly right.
Like the student solving the test alone.

| | Step 2 | Step 3 |
|---|---|---|
| Who decides how far to move? | we do (answer key) | the computer (tries all, picks best) |
| Purpose | prove the idea | actually solve the problem |
| Output | "yes, they match" | "turned 30°, zoom ×1.0" |

**Why test3/4/5 are not solved yet:** both photos are unrolled around their own MIDDLE.
test3 was also moved 20 px, so its middle is a DIFFERENT building → the flat pictures
don't match well → low peak, unsure answer. Step 4: try many middles, keep the best.

**One line each:**
- Step 1: make the puzzle + write the answer.
- Step 2: show "turned" = "flat picture moved" (using the answer).
- Step 3: computer finds how far it moved → turn + zoom.
- Step 4: computer also finds where the middle is → shift.
