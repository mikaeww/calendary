"""What Calendary needs from Windows: the Credential Manager as its keyring and its own taskbar identity.

Imported only on Windows (advapi32 and shell32 load at import). Credentials are generic ones named
`<service>/<account>`, kept for the user on this machine. Not for Linux, which uses keyring.py's Secret Service.
"""
import ctypes
from ctypes import wintypes

from calendary.errors import ServiceError

GENERIC = 1
PERSIST_LOCAL_MACHINE = 2
NOT_FOUND = 1168
APP_ID = "Calendary"


class _Credential(ctypes.Structure):
    _fields_ = [("Flags", wintypes.DWORD), ("Type", wintypes.DWORD), ("TargetName", wintypes.LPWSTR),
                ("Comment", wintypes.LPWSTR), ("LastWritten", wintypes.FILETIME),
                ("CredentialBlobSize", wintypes.DWORD), ("CredentialBlob", ctypes.POINTER(ctypes.c_ubyte)),
                ("Persist", wintypes.DWORD), ("AttributeCount", wintypes.DWORD), ("Attributes", ctypes.c_void_p),
                ("TargetAlias", wintypes.LPWSTR), ("UserName", wintypes.LPWSTR)]


_advapi = ctypes.WinDLL("advapi32", use_last_error=True)
_advapi.CredWriteW.argtypes = [ctypes.POINTER(_Credential), wintypes.DWORD]
_advapi.CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD,
                              ctypes.POINTER(ctypes.POINTER(_Credential))]
_advapi.CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
_advapi.CredFree.argtypes = [ctypes.c_void_p]
for _call in (_advapi.CredWriteW, _advapi.CredReadW, _advapi.CredDeleteW):
    _call.restype = wintypes.BOOL


def _failure(action):
    return ServiceError("Windows-Anmeldeinformationsverwaltung: %s fehlgeschlagen (Fehler %d)"
                        % (action, ctypes.get_last_error()))


class CredentialManager:
    """The same three calls as keyring.Keyring; `service` separates the app's items, tests pass their own."""

    def __init__(self, service="calendary"):
        self.service = service

    def _target(self, email):
        return "%s/%s" % (self.service, email)

    def store(self, email, token):
        blob = token.encode()
        buffer = (ctypes.c_ubyte * len(blob)).from_buffer_copy(blob)
        credential = _Credential(Type=GENERIC, TargetName=self._target(email), CredentialBlobSize=len(blob),
                                 CredentialBlob=buffer, Persist=PERSIST_LOCAL_MACHINE, UserName=email)
        if not _advapi.CredWriteW(ctypes.byref(credential), 0):
            raise _failure("Speichern")

    def lookup(self, email):
        """The stored secret, or None when there is none for this account."""
        found = ctypes.POINTER(_Credential)()
        if not _advapi.CredReadW(self._target(email), GENERIC, 0, ctypes.byref(found)):
            if ctypes.get_last_error() == NOT_FOUND:
                return None
            raise _failure("Lesen")
        try:
            return ctypes.string_at(found.contents.CredentialBlob, found.contents.CredentialBlobSize).decode() or None
        finally:
            _advapi.CredFree(found)

    def clear(self, email):
        if not _advapi.CredDeleteW(self._target(email), GENERIC, 0) and ctypes.get_last_error() != NOT_FOUND:
            raise _failure("Löschen")


def use_own_taskbar_entry():
    # Without an app id of its own, Windows groups the window under pythonw.exe and shows Python's icon.
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
