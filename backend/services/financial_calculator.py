from decimal import Decimal, ROUND_HALF_UP


TWO_DECIMAL_PLACES = Decimal("0.01")


def calculate_growth(
    previous_value: Decimal,
    current_value: Decimal,
) -> dict[str, Decimal]:
    if previous_value == 0:
        raise ValueError(
            "Percentage growth cannot be calculated from zero."
        )

    absolute_change = current_value - previous_value

    percentage_change = (
        absolute_change / previous_value
    ) * Decimal("100")

    rounded_percentage = percentage_change.quantize(
        TWO_DECIMAL_PLACES,
        rounding=ROUND_HALF_UP,
    )

    return {
        "previous_value": previous_value,
        "current_value": current_value,
        "absolute_change": absolute_change,
        "percentage_change": rounded_percentage,
    }