"""The one error type of the Google package; its message is German and shown to the user as is."""


class GoogleError(Exception):
    """A Google or keyring operation failed; `str()` says what happened and what to do."""
