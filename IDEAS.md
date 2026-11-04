# Ideas for Later

- Try other photos (more detail vs. less detail) and compare accuracy.
- Try very big rotations (180°) and big zooms (×4, ×8) to find the limits.
- Use log-polar for bottle cap rotation in the bottle inspection project.
- Add a test with noise or brightness change, to be more like a real second photo.
- Add a test with zoom smaller than 1 (×0.5, zoom out).
- Try more log-polar columns (512) to see if the zoom match gets better.
- Ignore the blurry left part (very near the center) when matching.
- Use the peak value as a "confidence" number: if peak < 0.1, say "not sure".
- Make a test with a BIG shift (e.g. 100 px) to show Step 3 really fails without Step 4.
- Make the search area bigger (±120 px) and test with a big shift (100 px).
- Search spots between pixels (sub-pixel) to get the shift more exact.
- Show a "difference picture" (white = mismatch) next to the red/cyan overlay.
- Use the step 5 overlay pictures in the report as the main result figure.
