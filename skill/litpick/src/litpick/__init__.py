"""litpick: open arXiv papers or local PDFs and look at their figures."""
__version__ = "2.0.0"

# Bump when the figure finder changes in a way that changes its output. Papers parsed by an
# older parser are parsed again the next time they are opened.
PARSER_VERSION = "2.1"
