# Data the Raman skill reads

| File | Contents | Source and licence |
|---|---|---|
| `crd_layered_modes.json` | 384 layered crystals from the Computational Raman Database v1.0.1: for each, the Raman modes visible in backscattering along the layer normal (position in cm-1, relative intensity, irrep, label), used by `match_library` | Bagheri and Komsa 2023, Sci. Data 10, 80, Materials Cloud Archive record 0m9r0-g3486, CC BY 4.0. Derived data: tensors rotated into the layer frame and reduced to observable modes by `scripts/build_crd_resource.py` |
| `reference_tables/*.json` | measured mode tables for 8 materials (2H-MoS2, 2H-MoSe2, 2H-WS2, 2H-WSe2, black phosphorus, CrSBr, graphene, hBN); every mode carries its paper (DOI or arXiv id) and a table, figure or page locator | the cited papers; numbers only |

Rebuild the CRD file from the raw database: `python scripts/build_crd_resource.py <folder with crd.json>`.
