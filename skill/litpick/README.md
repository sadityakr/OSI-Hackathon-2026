# litpick

Open arXiv papers or local PDFs, cut out every figure with its caption, keep them in a searchable
library on your own disk, and show any figure to Claude with a citation.

## Install (macOS, Windows, Linux)

1. Install uv once: https://docs.astral.sh/uv/getting-started/installation/
2. Install this folder as a Claude plugin. On first start, uv fetches Python and the dependencies.

The library lives in your user data folder (`~/Library/Application Support/litpick`,
`%LOCALAPPDATA%\litpick`, `~/.local/share/litpick`). Set `LITPICK_HOME` to put it elsewhere,
and `LITPICK_CONTACT` to your email so arXiv knows who is calling.

## Command line

    uvx --from . litpick ingest 2407.13230
    uvx --from . litpick figures 2407.13230
    uvx --from . litpick view 2407.13230 "Fig. 2" --out .
    uvx --from . litpick search "magnetoresistance field sweep"
    uvx --from . litpick status

## Develop

    uv run pytest -q                    # offline tests
    LITPICK_NETWORK=1 uv run pytest -q  # plus one real arXiv download
