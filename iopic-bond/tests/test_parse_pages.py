"""Page selection for the fast parse. No Docling and no PDF fixtures: the scanner is pure data."""
from iopic_bond.pdf.pages import (
    PageScan,
    append_text_pages,
    counts_as_figure_image,
    doc_page_map,
    remap_pages,
    select_layout_pages,
)
from iopic_bond.pdf.schema import BlockNode, Edge, Provenance
from iopic_bond.pdf.xref import resolve_internal_refs


def _pages(specs):
    return [PageScan(n, text, images, paths) for n, text, images, paths in specs]


def test_figure_page_keeps_its_neighbours_only():
    pages = _pages([
        (1, "Introduction\n", 0, 0),
        (2, "The shift, as shown in Fig. 2, is small.\n", 0, 2),
        (3, "Figure 2. Raman spectra of monolayer MoS2.\n", 1, 0),
        (4, "Methods and references follow.\n", 0, 0),
        (5, "More methods.\n", 0, 0),
        (6, "Still methods.\n", 0, 0),
        (7, "Appendix.\n", 0, 0),
        (8, "Bibliography.\n", 0, 0),
    ])
    # Page 3 is the figure; keep its neighbours. The "Fig. 2" mention on page 2 is a neighbour
    # here, but a mention alone, on a distant page, would not be selected.
    assert select_layout_pages(pages) == [2, 3, 4]


def test_distant_mention_is_not_a_layout_page():
    pages = _pages([
        (1, "see Fig. 2 for the spectrum, then more text.\n", 0, 0),
        (2, "nothing here\n", 0, 0),
        (3, "nothing here\n", 0, 0),
        (4, "\nFigure 2. Spectra.\n", 0, 40),
        (5, "nothing here\n", 0, 0),
        (6, "nothing here\n", 0, 0),
        (7, "nothing here\n", 0, 0),
        (8, "nothing here\n", 0, 0),
    ])
    assert select_layout_pages(pages) == [3, 4, 5]


def test_no_figure_evidence_parses_every_page():
    pages = _pages([(n, "plain text", 0, 0) for n in range(1, 6)])
    assert select_layout_pages(pages) == [1, 2, 3, 4, 5]


def test_small_saving_parses_every_page():
    pages = _pages([
        (1, "\nFigure 1. A plot.\n", 1, 0),
        (2, "text", 0, 0),
    ])
    # The figure's neighbour is the only other page, so a subset would not skip anything.
    assert select_layout_pages(pages) == [1, 2]


def test_logo_sized_image_does_not_count():
    assert not counts_as_figure_image(40, 40)
    assert not counts_as_figure_image(200, 30)
    assert counts_as_figure_image(220, 160)


def test_remap_and_text_layer_keep_figure_mentions():
    root = BlockNode(id="paper", type="document")
    figure = BlockNode(
        id="paper/fig1",
        type="figure",
        attrs={"label": "Figure 2", "caption_page": 1},
        prov=[Provenance(1, (0.0, 0.0, 10.0, 10.0), (0, 0))],
    )
    root.children.append(figure)
    remap_pages(root, {1: 7})
    assert figure.prov[0].page_no == 7
    assert figure.attrs["caption_page"] == 7

    text = append_text_pages(
        root,
        [PageScan(2, "The Raman modes are assigned in Fig. 2 of the supplement.", 0, 0)],
        "",
    )
    assert "Fig. 2" in text
    assert resolve_internal_refs(root) == 1
    mention = root.children[-1]
    assert mention.prov[0].page_no == 2
    assert mention.edges[0] == Edge(
        type="references-figure",
        target="paper/fig1",
        marker_span=mention.edges[0].marker_span,
    )


def test_page_map_rejects_a_short_document():
    class Doc:
        pages = {1: None}

    assert doc_page_map(Doc(), [3, 4]) is None
    assert doc_page_map(Doc(), [4]) == {1: 4}
