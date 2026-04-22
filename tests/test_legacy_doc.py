from doclift.legacy_doc import extract_references, extract_tables


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
