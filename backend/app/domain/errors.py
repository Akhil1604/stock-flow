class DomainError(Exception):
    """Base class for expected business-rule failures."""


class ProductNotFound(DomainError):
    pass


class InsufficientInventory(DomainError):
    pass


class InvalidOrder(DomainError):
    pass


class OrderNotFound(DomainError):
    pass


class OrderAlreadyCancelled(DomainError):
    pass
