"""The error every provider raises; its message is already in the interface language and shown as is."""


class ServiceError(Exception):
    """A provider, network or keyring operation failed; `str()` says what happened and what to do."""
