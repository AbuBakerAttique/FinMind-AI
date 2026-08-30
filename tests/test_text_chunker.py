import pytest

from backend.services.text_chunker import chunk_text


def test_empty_text_returns_no_chunks():
    result = chunk_text("")

    assert result == []


def test_whitespace_only_text_returns_no_chunks():
    result = chunk_text("   \n\t   ")

    assert result == []


def test_short_text_returns_one_chunk():
    result = chunk_text(
        "Revenue increased during the financial year."
    )

    assert result == [
        "Revenue increased during the financial year."
    ]


def test_text_is_split_into_overlapping_chunks():
    result = chunk_text(
        "one two three four five",
        chunk_size=13,
        overlap=5,
    )

    assert result == [
        "one two three",
        "three four",
        "four five",
    ]


def test_chunks_respect_character_limit():
    result = chunk_text(
        "Revenue increased while operating expenses "
        "decreased and profit improved.",
        chunk_size=25,
        overlap=5,
    )

    assert len(result) > 1

    for chunk in result:
        assert len(chunk) <= 25


def test_chunk_size_must_be_greater_than_zero():
    with pytest.raises(
        ValueError,
        match="chunk_size must be greater than zero",
    ):
        chunk_text(
            "Some financial text",
            chunk_size=0,
        )


def test_overlap_cannot_be_negative():
    with pytest.raises(
        ValueError,
        match="overlap must be between 0 and chunk_size",
    ):
        chunk_text(
            "Some financial text",
            overlap=-1,
        )


def test_overlap_must_be_smaller_than_chunk_size():
    with pytest.raises(
        ValueError,
        match="overlap must be between 0 and chunk_size",
    ):
        chunk_text(
            "Some financial text",
            chunk_size=100,
            overlap=100,
        )