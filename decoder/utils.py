import logging

logger = logging.getLogger(__name__)


def check_luhn(number: int) -> bool:  # Luhn check
    return check_luhn(str(number))


def check_luhn(number: str, check_digit: int = 0) -> bool:  # Luhn check
    digits = list(map(int, number))
    return check_digit == sum(digits + [d + (d > 4) for d in digits[-2::-2]]) % 10
