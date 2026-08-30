from decimal import Decimal

import pytest

from backend.services.financial_calculator import calculate_growth


def test_calculates_apple_sales_growth():
    result = calculate_growth(
        previous_value=Decimal("391035"),
        current_value=Decimal("416161"),
    )

    assert result["previous_value"] == Decimal("391035")
    assert result["current_value"] == Decimal("416161")
    assert result["absolute_change"] == Decimal("25126")
    assert result["percentage_change"] == Decimal("6.43")


def test_calculates_negative_growth():
    result = calculate_growth(
        previous_value=Decimal("100"),
        current_value=Decimal("75"),
    )

    assert result["absolute_change"] == Decimal("-25")
    assert result["percentage_change"] == Decimal("-25.00")


def test_calculates_zero_growth():
    result = calculate_growth(
        previous_value=Decimal("500"),
        current_value=Decimal("500"),
    )

    assert result["absolute_change"] == Decimal("0")
    assert result["percentage_change"] == Decimal("0.00")


def test_rounds_percentage_to_two_decimal_places():
    result = calculate_growth(
        previous_value=Decimal("3"),
        current_value=Decimal("4"),
    )

    assert result["percentage_change"] == Decimal("33.33")


def test_rejects_zero_previous_value():
    with pytest.raises(
        ValueError,
        match="Percentage growth cannot be calculated from zero",
    ):
        calculate_growth(
            previous_value=Decimal("0"),
            current_value=Decimal("100"),
        )