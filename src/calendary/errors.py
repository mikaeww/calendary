"""The error every provider raises; its message is German and shown to the user as is."""


class ServiceError(Exception):
    """A provider, network or keyring operation failed; `str()` says what happened and what to do."""
