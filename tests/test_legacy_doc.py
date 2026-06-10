from pathlib import Path

from doclift.legacy_doc import (
    FigureAsset,
    classify_document,
    extract_references,
    extract_tables,
    extract_title,
    link_related_assets,
    text_quality_flags,
)


def test_extract_references_dedupes() -> None:
    refs = extract_references("See Table 1 and table 1 and Table 2.", r"\bTable\s+\d+\b")
    assert refs == ["Table 1", "Table 2"]


def test_extract_tables_parses_tabbed_rows() -> None:
    text = "\n".join(
        [
            "Intro",
            "Table 1. Example caption",
            "",
            "Metric\tRest\tSwim",
            "O2\t1.0\t2.0",
            "CO2\t0.5\t1.1",
        ]
    )
    tables = extract_tables(text)
    assert len(tables) == 1
    assert tables[0].caption == "Table 1. Example caption"
    assert tables[0].column_count_guess == 3
    assert tables[0].parsed_rows[1] == ["O2", "1.0", "2.0"]


def test_link_related_assets_matches_explicit_figure_refs() -> None:
    assets = [
        FigureAsset(
            asset_id="a1",
            path="/tmp/Fig. 5.1.bmp",
            relative_path="vol/Fig. 5.1.bmp",
            name="Fig. 5.1.bmp",
            container="vol",
            looks_like_figure=True,
        ),
        FigureAsset(
            asset_id="a2",
            path="/tmp/Slide 1.jpg",
            relative_path="vol/Slide 1.jpg",
            name="Slide 1.jpg",
            container="vol",
            looks_like_figure=False,
        ),
    ]
    matched = link_related_assets(["Fig. 5.1"], assets)
    assert [asset.asset_id for asset in matched] == ["a1"]


def test_extract_title_prefers_exam_headers() -> None:
    text = "\n".join(
        [
            "EXAM I",
            "February 25, 1999",
            "Answer three of the following essay questions.",
        ]
    )
    assert extract_title(text, "fallback") == "EXAM I"


def test_extract_title_handles_cover_sheet() -> None:
    text = "\n".join(
        [
            "MARB 401",
            "PHYSIOLOGICAL ECOLOGY",
            "OF",
            "MARINE MAMMALS",
            "CLASS NOTES",
            "SPRING 2000",
        ]
    )
    assert extract_title(text, "fallback") == "PHYSIOLOGICAL ECOLOGY OF MARINE MAMMALS"


def test_classify_document_kinds() -> None:
    assert classify_document("EXAM II\nApril 6, 1999\n", Path("Exam II-99.doc")) == "exam"
    assert classify_document("FINAL EXAM SPRING 1999\nAnswer 3 questions\n", Path("final exam.991.doc")) == "final_exam"
    assert classify_document("MARB 401\nPHYSIOLOGICAL ECOLOGY\nOF\nMARINE MAMMALS\nCLASS NOTES\n", Path("COVER.doc")) == "cover_notes"
    assert classify_document("SPRING 2000\nMARB 401\nPhysiological Ecology of Marine Mammals\n", Path("Syllabus 401.001.doc")) == "syllabus"


def test_text_quality_flags_detect_binary_residue_and_bad_title() -> None:
    raw = "\x01\x02\x03þ7#$\x19\x01.Ó>\nThe Incredible Shrinking Theory\n" + ("normal words " * 20)
    flags = text_quality_flags(raw, title="þ7#$\x19\x01.Ó>")
    assert "control_character_residue" in flags
    assert "suspicious_title" in flags
