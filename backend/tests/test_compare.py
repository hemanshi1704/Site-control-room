from decimal import Decimal

from eval.compare import lenient_match, strict_match


def test_extra_column_passes_lenient_only():
    expected = [("Udaipur Lake Villas",)]
    got = [("Udaipur Lake Villas", Decimal("31.5"))]
    assert not strict_match(got, expected)
    assert lenient_match(got, expected)


def test_wrong_answer_fails_both():
    expected = [("Udaipur Lake Villas",)]
    got = [("Kota Metro Mall", 12.0)]
    assert not strict_match(got, expected) and not lenient_match(got, expected)


def test_row_count_must_match():
    assert not lenient_match([("a", 1), ("b", 2)], [("a",)])


def test_wrong_pairing_fails_lenient():
    expected = [("a", 1.0), ("b", 2.0)]
    assert lenient_match([("a", 1.0, "x"), ("b", 2.0, "y")], expected)
    assert not lenient_match([("a", 2.0), ("b", 1.0)], expected)


def test_ranking_order_matters_when_ordered():
    expected = [("a", 3.0), ("b", 2.0)]
    assert not lenient_match([("b", 2.0), ("a", 3.0)], expected, ordered=True)
    assert lenient_match([("b", 2.0), ("a", 3.0)], expected, ordered=False)


def test_extra_rank_column_in_ranking():
    expected = [("a", 3.0), ("b", 2.0)]
    got = [(1, "a", 3.0), (2, "b", 2.0)]
    assert lenient_match(got, expected, ordered=True)


def test_number_rounding_and_empty():
    assert strict_match([(Decimal("3.7083333"),)], [(Decimal("3.7083333333"),)])
    assert lenient_match([], [])
    assert not lenient_match([("x",)], [])
