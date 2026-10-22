# Using the literature: find the reference spectrum, look at it, compare

Use literature after you have a material hypothesis, to confirm assignments and to show the user a published
reference spectrum next to theirs. Literature tools may be absent in some sessions; then rely on
`materials.md` and `relations.md` and say so under limits.

## Steps
Use the iopic-bond skill in this plugin. Its script is `scripts/ib.py` in the sibling skill folder
`iopic-bond` (the `skills` directory that also holds this skill). Do not call Valency tools yourself.

1. **Known paper: open it.** When this note already gives an arXiv id, run `ib.py ingest <arxiv_id>`. Skip
   search. A paper already in the library returns at once.
2. **Library before search.** If you do not yet have an id, run `ib.py library "<concept>"`. On a hit, run
   `ib.py figures <arxiv_id>` and `ib.py view <arxiv_id> "Fig. N"`.
3. **Concept search, never peak positions.** If the library has nothing, run `ib.py find "<concept>"`. The
   query is a concept, such as "Raman spectroscopy of monolayer WS2 layer dependence" or "polarized Raman
   CrSBr phonon modes". Numbers and peak positions do not help. Prefer a result whose id is an arXiv id,
   then `ib.py ingest` that id.
4. **List and choose.** `ib.py figures` gives captions and the paragraphs that discuss each figure. Pick the
   figure whose caption shows spectra of the material under comparable conditions (laser, layer count,
   temperature).
5. **Look at it.** `ib.py view` writes a PNG (`saved_png`) and prints `image_path`. Read that image. Read the
   peak positions and relative intensities off it, state that they are read from a figure (about +-1 cm-1),
   and compare with the fitted peaks.
6. **Cite precisely.** Author, year, journal or arXiv id, and the figure or table number for every literature
   number. Never cite a paper you have not retrieved in this session as the source of a specific number;
   numbers in `materials.md` already carry verified sources.

## Good reference figures (arXiv, verified to show the named content)
- MoS2 layers: Lee et al. 2010, arXiv 1005.2509, Fig. 2a (spectra 1L to bulk), Fig. 2b (positions vs layers).
- MoS2 strain: Conley et al. 2013, arXiv 1305.3880, Fig. 2.
- Graphene layers: Ferrari et al. 2006, arXiv cond-mat/0606284, Fig. 2. Defects: Cancado et al. 2011, arXiv
  1105.0175. Strain: Mohiuddin et al. 2009, arXiv 0812.1538, Figs. 2, 3.
- MoSe2: Nam et al. 2015, arXiv 1511.01225, Fig. 2. WSe2: Sahin et al. 2013, arXiv 1303.5861, Fig. 2a.
- hBN: Gorbachev et al. 2011, arXiv 1008.2868, Fig. 4. Black phosphorus: Castellanos-Gomez et al. 2014, arXiv
  1403.0499, Fig. 3b.
- CrSBr: Mondal et al. 2025, arXiv 2410.22164, Fig. 2a,b (polarized, two lasers); Pawbake et al. 2023, arXiv
  2211.12939, Fig. 1c (bulk).
- Si second order: Gillet et al. 2017, arXiv 1708.05874, Fig. 1.
