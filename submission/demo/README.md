# Demos: CrSBr thickness and CrSBr defects (skill v4)

Two recorded demos of the Raman skill (v4) on held-out or new data, with the dry runs that prepared them.

| Folder | Contents |
|---|---|
| `crsbr-thickness/data/` | six spectra of held-out case `int-CrSBr-thickness-01` (Zenodo 15048152, Wdowik et al. 2025, CC BY 4.0); no answer key |
| `crsbr-thickness/` | notebook and HTML from dry run 4 (prompt below), plus a copy with code hidden |
| `crsbr-defects/data/` | one 4L CrSBr flake, untreated and after three He+ doses, laser along a and b (Figure 2a/2b of Czech repository DOI 10.48700/72gk1-7mb53, Sahu et al. 2026, CC BY 4.0); each spectrum normalised to its maximum because the deposited E along a sheet carries the figure's display factors |
| `crsbr-defects/` | notebook and HTML from dry run 3, plus a copy with code hidden |
| `config/` | the MCP config, read-deny settings and run scripts used for the recorded runs, and `make_defect_demo.py` (exports the defect spectra from the downloaded repository files) |

The recorded runs used iopic-Bond, the predecessor of litpick, as the literature server; litpick now serves the
same figures. The skill they loaded is the one in `../skills/raman-analysis/`.

Truth the agent never sees: thickness AFM order C 1L < E 2L < A 3L < F 5L < D 6L < B bulk; defect steps 1 to 3 are
He+ doses 3.9e13, 2.4e14 and 1.2e15 cm-2. Both source papers are in `data/test_set/withheld_papers.txt`.

## Prompts

- Thickness: "Here are Raman spectra of six CrSBr flakes exfoliated from the same crystal, all measured with the
  same settings (532 nm, room temperature). I want to know how thick each flake is."
- Defects: "Here are Raman spectra of a 4-layer CrSBr flake before and after three processing steps, each measured
  with the laser polarised along the a and the b axis. What changed, and is the material still good for a device?"

## Dry runs (Sonnet 5.5, headless, Oct 22; transcripts not published)

| Run | Change | Outcome |
|---|---|---|
| 1 | first try | skill triggered; stopped after the fits and offered the rest; no figure, no notebook |
| 2 | SKILL.md: finish the whole workflow in one turn | figures opened (thickness Fig. 1; defects Figs. 2 and 3 of Torres 2022); notebook blocked because don't-ask mode denied a `cp` |
| 3 | accept-edits mode | notebooks and HTML for both; defects answer in `dryruns/dryrun3-defects-answer.md` |
| 4 | thickness prompt asks for thickness | per-band fits give Ag1 C 103.1, E 103.3, A 108.6, F 111.9, D 113.3, B 114.0 cm-1; A < F < D < B ranked as AFM; C and E left "not determinable" because their Ag1 lies below the 1.58 eV monolayer value of Torres Fig. 1h |

The `.py` notebooks point at the figure in the local paper library of the computer that ran them, so open the
HTML exports to see the published figure next to the data. Figures are from Torres et al. 2022 (arXiv 2212.01754); check its licence before
publishing an export.
