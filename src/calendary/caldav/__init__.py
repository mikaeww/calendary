"""iCloud calendars over CalDAV: discovery, iCalendar reading and writing, local recurrence expansion (ADR 0005).

Everything here blocks on the network; callers run it on worker threads. No caching.
"""
from calendary.caldav.account import ICloudAccount, account_key, apple_id_of, is_icloud

__all__ = ["ICloudAccount", "account_key", "apple_id_of", "is_icloud"]
