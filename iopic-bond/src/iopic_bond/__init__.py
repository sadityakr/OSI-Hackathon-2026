"""iopic-Bond: a local MCP server that wraps Valency Bond and adds what Bond lacks.

Bond finds papers; iopic-Bond downloads their arXiv PDFs, parses each into a graph (``tree.json``:
sections, paragraphs, figures, "Fig. N" reference edges), keeps every parse in a local library so no
paper is parsed twice, and serves the figures to the model (image content) and to the person (an
MCP Apps panel). Design: ``docs/iopic-bond.md`` in the RamanLens repo; usage: ``README.md``.

Input: a Valency API token (``VALENCY_BOND_TOKEN``) and network access to Bond and arXiv.
Process: Bond search -> arXiv fetch -> Docling parse -> SQLite-indexed library -> MCP tools.
Output: an MCP server (``iopic-bond serve``) plus the library folder under ``IOPIC_BOND_HOME``.
"""

__version__ = "0.1.0"
