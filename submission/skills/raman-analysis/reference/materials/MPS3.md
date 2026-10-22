# MPS3 (FePS3, MnPS3, NiPS3, CoPS3): expert Raman notes

Numbers as printed in the cited source. "journal p." = page of the published journal PDF. Peak labels P1, P2, ...
are paper-specific (ordered by frequency within each paper), so the same label means different modes in different
papers: always map by frequency. Not used by design: the papers behind Zenodo 23300631 (NiPS3) and 20449397 (CoPS3).

## Shared structure and irreps
- Bulk monoclinic C2h; Gamma = 8Ag + 7Bg + 6Au + 9Bu (NiPS3). Backscattering: Ag and Bg in XX, only Bg in XY. Monolayer
  is D3d (Kim et al. 2019, Nat. Commun. 10, 345, arXiv 1901.10890, journal p.2).
- High-frequency modes (above about 200 cm-1) are internal (P2S6)4- vibrations common to the family; low-frequency
  modes involve the metal ion and are the magnetically sensitive ones (Kim 2019, journal p.2; Vaclavkova et al. 2021,
  PRB 104, 134437, arXiv 2108.10945, journal p.2).
- Magnetic types (consensus framing): FePS3 Ising, NiPS3 XXZ (XY-like), MnPS3 Heisenberg (Lim et al. 2021, Curr.
  Appl. Phys. 21, 1, doi:10.1016/j.cap.2020.09.017, journal p.3).
- Three mechanisms for magnetic signatures: zone folding by the AFM supercell, spin-phonon / spin-spin interactions,
  and interference of phonons with electronic transitions (Fano) (Oliva et al. 2023, PRB 107, 104415,
  doi:10.1103/physrevb.107.104415, journal p.2). In MnPS3 the magnetic and chemical cells coincide, so no zone folding.

## FePS3 (T_N about 118 to 120 K)
- Above T_N a broad low-frequency band (about 105 cm-1, "P0") plus four modes 150 to 400 cm-1; below T_N it resolves
  into sharp zone-folded peaks P1 to P3 and P4 gains intensity; a magnon-gap mode M appears (Ghosh et al. 2021, PRB
  103, 064431, doi:10.1103/physrevb.103.064431, journal p.1-2; Vaclavkova 2021, journal p.2, Fig. 1a).
- Magnon at 121 cm-1 (about 15 meV, matches neutron data), blueshifting on cooling (Liu et al. 2021, PRL 127, 097401,
  doi:10.1103/physrevlett.127.097401, journal p.2; 4L). In few layers it was seen only well below T_N (about 60 K)
  near 120 cm-1 (Ghosh 2021, journal p.1).
- Field along c: M splits into branches; the lower branch anticrosses P1 to P3 (magnon-polarons), and an extra R1 mode
  appears at high field (Vaclavkova 2021, journal p.3, Fig. 1b; Liu 2021, up to 30 T).
- Thickness: DISPUTED. Lee et al. 2016 (Nano Lett. 16, 7433, arXiv 1608.04169) report Ising order to 1L with little
  T_N change; Wang et al. 2016 (2D Mater. 3, 031009) report a T_N drop with thinning (both relayed by Martin-Perez
  et al. 2023, ACS Nano, doi:10.1021/acsnano.2c11654, journal p.2). Magnetometry on 5 to 9 layer flakes gives T_N
  about 4 K below bulk (114.3 versus 118 K) (Martin-Perez 2023, journal p.5). Strain alone can lower T_N (same, p.2).
- Air: 2L FePS3 Raman stable up to 6 days in ambient (Lee 2016, Suppl. Fig. S16, journal p.38).

## MnPS3 (T_N about 78 K)
- Mode near 155 cm-1 involves Mn; it disappears near 80 K and a mode at 151 cm-1 appears below about 50 K (130L flake,
  488 nm, 0.17 mW to avoid heating) (Sun et al. 2019, J. Phys. Chem. Lett. 10, 3087, doi:10.1021/acs.jpclett.9b00758,
  journal p.2, p.4-5). Sun et al. also infer transitions near 120, 80 and 55 K (journal p.2).
- T_N from broadening, abrupt redshift and spectral-weight gain of the 155 cm-1 peak: about 78 K bulk, about 66 K 3L
  (Lim 2021, journal p.2, p.11).
- Frequencies are nearly constant from 2L to bulk (weak interlayer coupling); 3L-4L show only P5, P6; 2L only P6; 1L
  gave no signal (degradation or weak scattering) (Sun 2019, journal p.3-4).
- Below T_N (Oliva 2023, 3.4 K): a mode near 117 cm-1 vanishes and new peaks appear near 194, 370, 565, 605 cm-1, of
  unknown origin; the mode near 154 cm-1 is the most T-sensitive. Its two-magnon interpretation is ruled out
  (two-magnon expected near 177 cm-1); origin DISPUTED (Oliva 2023, journal p.4, p.7-8).
- A spin-glass-like short-range regime below about 120 K is proposed from linewidths (Oliva 2023, journal p.6).

## NiPS3 (bulk T_N 155 K)
- P2 (near 180 cm-1) splits into Ag (XX, higher) and Bg (XY, lower) below T_N; Delta P2 tracks the susceptibility and
  is near zero at 295 K (Kim 2019, journal p.4-5, Fig. 4). Two-magnon continuum in XY grows and blueshifts on cooling;
  the Fano asymmetry |1/q| of a high-frequency phonon (P9) rises below T_N (Kim 2019, journal p.3-5, Fig. 3).
- Thickness: order persists to 2L with slightly lower T_N; Kim 2019 conclude it is suppressed in 1L (same on hBN and
  SiO2). DISPUTED: Kim T. Y. et al. 2021 (Nano Lett. 21, 10114, doi:10.1021/acs.nanolett.1c03992, journal p.2, p.5)
  argue 1L orders but the D3d monolayer's three zigzag domains make Delta P2 unmeasurable in XX/XY. Discala et al.
  2024 (Adv. Phys. Res. 3, 2300096) also question bulk-Hamiltonian assumptions (journal p.1-2).
- Multiphonon peaks near 210, 590, 800 cm-1 are resonance dependent and not magnetic (Kim 2019, journal p.4).

## CoPS3
- Monolayer about 0.80 nm. P2 near 149 cm-1 splits into P2' (Ag) and P2'' (Bg) at low T (XY vs XX); Delta P2 > 8 cm-1
  below about 56 K, near zero above about 100 K; bulk transition 118 K (Liu Q. et al. 2021, PRB 103, 235411,
  doi:10.1103/physrevb.103.235411, journal p.3-4, Figs. 2-3). Splitting is layer independent (intralayer distortion).
- Two-magnon bands near 350 and 600 cm-1 in XY in 1L; Fano P8 below 56 K (Liu 2021, journal p.4-5, Fig. 4). The
  authors interpret few-layer behaviour as BKT-like (T_KT about 100 K); interpretation, not consensus.

## Polarization, excitation, quality
- Use XX and XY (or LL / LR) on the same spot; splitting modes (NiPS3 P2, CoPS3 P2) are only separable this way.
- Resonance changes multiphonon intensities (Kim 2019) and Raman markers of T_N are laser-wavelength sensitive
  (Martin-Perez 2023, journal p.2).

## Pitfalls
- Laser heating: local heating can suppress order and shift the apparent T_N; low power and power series are needed
  (Martin-Perez 2023, journal p.2; Sun 2019 used 0.17 mW).
- Label confusion (P2 at 117 vs 155 cm-1 in different MnPS3 papers).
- Absence of a splitting in 1L is not proof of no order (Kim 2021 domain argument).

## What to ask
- Temperature series and its spacing around T_N; laser power and wavelength; polarization configuration.
- Layer number and substrate; strain; time in air; field direction if magnons are claimed.

## Reference figures
- arXiv 1901.10890 (Kim 2019, NiPS3) Fig. 3: two-magnon versus T and thickness; Fig. 4: Delta P2 versus T; Fig. 5:
  T_N versus thickness.
- arXiv 2108.10945 (Vaclavkova 2021, FePS3) Fig. 1: T map 4.2 to 300 K and magneto-Raman magnon-phonon coupling.
- doi:10.1103/physrevb.103.235411 (Liu 2021, CoPS3) Figs. 3-4: P2 splitting and two-magnon (arXiv id not verified).
