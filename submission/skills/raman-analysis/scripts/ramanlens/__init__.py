"""RamanLens: a Raman interpretation agent with cited relations and figure-level literature grounding."""

from pathlib import Path

__version__ = "0.0.1"

# Data the package reads (literature mode tables, the precomputed CRD mode library) lives in the skill's
# resources/ folder, next to scripts/ which holds this package: raman-analysis/scripts/ramanlens/__init__.py.
RESOURCES = Path(__file__).resolve().parents[2] / "resources"
