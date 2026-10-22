# Relations: equation, validity, source

Apply only inside the validity range; otherwise say the relation does not apply and why. Relations marked (rl.py)
are implemented: `python rl.py list_relations` shows their inputs and units, `python rl.py apply_relation --name
<name> --inputs '<json>'` applies one and refuses out-of-range inputs, returning the reason. Apply the others by
hand from the equation here and say so in the report. Also listed: `crsbr_ag_mode_assignment_with_polarization_axis`
(rl.py; Mondal et al. 2025, arXiv 2410.22164).

| name | gives | equation (all variables defined) | validity | source |
|---|---|---|---|---|
| `graphene_defect_distance_from_ID_IG` (rl.py) | inter-defect distance L_D (nm), defect density n_D (cm-2) | L_D^2 = (1.8+-0.5)e-9 lambda_L^4 / (I_D/I_G); n_D = (1.8+-0.5)e22 / lambda_L^4 * (I_D/I_G); lambda_L laser wavelength in nm, I_D/I_G ratio of peak heights | point defects, low-defect regime (L_D >= 10 nm, G FWHM about 14 cm-1), visible lasers | Cancado et al., Nano Lett. 11, 3190 (2011), arXiv 1105.0175 |
| eckmann defect type (apply by hand) | defect type | I_D/I_D' about 13 sp3, about 7 vacancy, about 3.5 boundary | low defect density; doping lowers D and D' intensities (Bruna et al. 2014, arXiv 1405.4264) | Eckmann et al., Nano Lett. 12, 3925 (2012), arXiv 1207.2058 |
| `graphene_strain_doping_from_G_2D` (rl.py) | strain epsilon and hole density | vector decomposition of (omega_G, omega_2D) from origin (1581.6, 2676.9) cm-1 along strain slope 2.2+-0.2 and hole-doping slope 0.70+-0.05 | 1L graphene, 514.5 nm only (2D disperses with laser), hole doping (electron doping nonlinear) | Lee et al., Nat. Commun. 3, 1024 (2012), arXiv 1209.0234 |
| `graphene_layers_from_2D_shape` (rl.py) | 1L vs few-layer | 1L: single Lorentzian 2D (FWHM about 25 cm-1 at 514.5 nm); 2L: four components | exclude turbostratic graphite (single but about 2x wider, +20 cm-1) | Ferrari et al., PRL 97, 187401 (2006); Lee 2012 |
| `mos2_layer_number_from_separation` (rl.py) | layer number N | Delta = omega(A1g) - omega(E2g1): 19.1 (1L), 21.4 (2L), 23.1 (3L), 24.3 (4L), 25.2 (bulk) cm-1 | 2H-MoS2, 514.5 to 532 nm, SiO2/Si; resolution better than about 1 cm-1 in Delta; strain and doping shift Delta | Lee et al., ACS Nano 4, 2695 (2010), Fig. 2b |
| `ws2_layer_number_from_separation` (rl.py) | layer number trend | A1g 417.2 (1L), 418.4 (2L), 419.0 (3L), 420.1 (bulk) cm-1 at 514.5 nm; fit 2LA(M) and E2g1 separately | 2H-WS2, 514.5 nm; calibrate with Si | Berkdemir et al., Sci. Rep. 3, 1755 (2013), Table 1 |
| linear chain (apply by hand) | layer number from shear (C) or breathing (LB) mode | omega_C(N) = omega_C(bulk) * sqrt(1 + cos(pi/N)) / sqrt(2); omega_LB(N) with sqrt(1 - cos(pi/N)) | any layered material, needs low-frequency setup (below about 50 cm-1); even and odd N have different active modes | Zhang et al., PRB 87, 115413 (2013), arXiv 1212.6796 |
| MoS2 strain vs doping (apply by hand) | strain vs doping, qualitative to semi-quantitative | E' -4.5 cm-1/% uniaxial strain (A' unshifted); A1g -4 cm-1 at 1.8e13 cm-2 electrons (E2g1 about -0.6) | 1L and 2L MoS2 | Conley et al. 2013; Chakraborty et al. 2012 |
| heating check (apply by hand) | laser heating estimate | Delta_omega = chi * Delta_T; chi(graphene G) about -0.016 cm-1/K; 1L WS2 -0.0093 (E), -0.0122 (A1g); few-layer MoS2 about -0.013 (E2g), -0.012 (A1g) | linear near room temperature | Calizo et al. 2007; Huang et al. 2016; Sahoo et al. 2013 |
