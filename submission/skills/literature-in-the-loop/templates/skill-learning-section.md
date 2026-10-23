<!-- Paste into the generated SKILL.md. Replace <technique> and adapt the examples; keep the rules. -->

**Required first action (add to the list at the top of SKILL.md):** find the setup. Match the data files against
the fingerprints in `${CLAUDE_SKILL_DIR}/setups/*/setup.md` and read the matching `setup.md` and
`calibration.json`. With no match or several, ask the user which instrument was used (or, unattended, state the
assumption and continue); for a new instrument copy `setups/_template/` to `setups/<setup-id>/` and fill what the
files and the user tell you.

N. **Learn from this run** (last step; skip it entirely when `SKILL_LEARNING=off` is set in the environment).
   Read `${CLAUDE_SKILL_DIR}/learned/README.md` once, then:
   - **Setup items** (an artifact of this instrument, a calibration offset, a default that works here): write them
     to `setups/<setup-id>/setup.md` now, with dataset and date; add calibration measurements to
     `calibration.json`.
   - **Technique and material items** (a caveat the notes lack, a technique that resolved an ambiguity, a paper
     that explained an anomaly, a disagreement with a note): append one entry each to `learned/inbox.md` in its
     entry format. Check the inbox first: if the same observation is already there from an independent dataset,
     add this run as a second occurrence instead of a new entry.
   - **Promote** an inbox item into `reference/` or `resources/` only when a paper confirms it (with locator) or it
     has recurred on two independent datasets; follow `learned/README.md`, append rather than rewrite, and log the
     promotion in `learned/CHANGELOG.md`.
   - End the answer with a short "Skill updates" list: each item captured or promoted, with the file it went to.
   Capture only what a future run would act on. Restating what the notes already say is not learning.
