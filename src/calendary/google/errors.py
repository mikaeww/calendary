"""Google's errors are service errors; the subclass only says where they came from."""
from calendary.errors import ServiceError


class GoogleError(ServiceError):
    """A Google operation failed; `str()` says what happened and what to do."""
