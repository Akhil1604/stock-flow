from enum import StrEnum


class OrderStatus(StrEnum):
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"


def validate_customer_email(email: str) -> None:
    if "@" not in email or email.startswith("@") or email.endswith("@"):
        raise ValueError("customer_email must be a valid email address")
