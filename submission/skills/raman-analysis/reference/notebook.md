# Writing the analysis notebook (Marimo)

The notebook is the deliverable: a researcher reruns it, sees how every number was produced, and checks every
citation. Start from the template; do not write the notebook from scratch.

## Steps

1. Copy `${CLAUDE_SKILL_DIR}/templates/raman_notebook.py` next to the data as `raman_analysis.py`.
2. Edit only the eight cells marked `FILL`:
   1. **Sample, conditions, data**: `SAMPLE` (material, substrate, laser, temperature, the user's question, what
      you assumed, the setup id from `setups/` and the caveats from its `setup.md` that apply), `SPECTRA` (label, file, series value or None), `SERIES` (name and unit of what varies),
      `BANDS` (search windows for the bands to track, from the material note), `MIN_SNR`.
   2. **Literature for this system**: `LIT_VALUES` (each reported number you compare with: quantity, band, value,
      uncertainty, source, figure or table locator, reference number) and `FIGURES` (the `image_path` from
      litpick `view_figure`, caption, reference number).
   3. **Method notes**: each analysis choice that came from a paper, with its reference number.
   4. **Interpretation**: five to ten bullets, most likely reading first, then alternatives and the measurement
      that would decide. Each bullet is one claim, tagged `[measured]`, `[inferred]`, `[literature]` or `[learned]`
      (an observation promoted from earlier runs; cite its `learned/CHANGELOG.md` date), with the number it rests
      on and its reference. Write numbers through `pos("label", "band")` inside the f-string so
      they come from the fit, never typed by hand.
   5. **Limits and questions** for the user (AFM, polarization, calibration lamp, laser power) and why.
   6. **References**: numbered, authors, year, title, journal or arXiv id, with a link
      (`https://arxiv.org/abs/<id>` or `https://doi.org/<doi>`).
   7. **Skill updates**: what this run added to the skill (setup note, learning inbox, promotions), from workflow
      step 12; "none" when nothing was added or `SKILL_LEARNING=off`.
   8. **TL;DR** (written last, shown right after the question, conditions, assumptions and setup panel): three
      to five bullets for a reader who reads nothing else, human or agent: the answer to the question, the key
      numbers through `pos(...)`, the confidence (high, moderate or low) and what it rests on, the main caveat,
      and the next measurement. Tagged like the interpretation, and only claims that sections 4 to 8 support.
3. Run `marimo export html raman_analysis.py -o raman_analysis.html --no-include-code`, then
   `python -c "import raman_analysis as r; r.app.run()"` from the same folder. Fix and rerun until both finish
   without errors. Look at the band table: a band reported as not resolved, or a fitted width far above the
   others, means the window or `MIN_SNR` needs adjusting.
4. The report is `raman_analysis.html` from step 3: code hidden, TL;DR at the top, results below. The method
   (baseline, windows, cutoffs) stays in `raman_analysis.py`, where every cell keeps `hide_code=True`; keep that
   decorator on any cell you add. Give the user both paths and `marimo edit raman_analysis.py` to open the live
   notebook, where each cell's code is one click away.

The computed cells already do: raw spectra, quality and Si calibration per spectrum, windowed band fits with Si
correction, band positions across the series, and the literature table with figures. Change them only when the
analysis needs something they do not do (for example a polarization series); keep each change in its own cell.

## Citation rules

- Never cite from memory. A number with a citation comes from a figure you viewed, a table in a reference note, or
  a paper you ingested this session, with its figure or table locator.
- Cite the paper that reports the number, not a review that repeats it, unless the review is all you opened.
- When two papers disagree, show both values and say so.

## Marimo rules (break the notebook when ignored)

- Every global name is defined in exactly one cell. Names local to a cell start with an underscore (`_fig`).
- A cell's arguments are the names it uses from other cells; its return tuple lists the names it defines.
  Never mutate another cell's object; build a new name.
- The last expression of a cell is what it shows (`mo.md(...)`, a figure, `mo.ui.table(rows)`).
