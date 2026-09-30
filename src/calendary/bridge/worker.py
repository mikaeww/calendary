"""Runs blocking jobs on threads and hands their results back to the GUI thread. Not for scheduling or retries."""
import threading
import traceback

from PySide6.QtCore import Property, QObject, Signal

from calendary.google.errors import GoogleError


class Worker(QObject):
    busyChanged = Signal()
    failed = Signal(str)
    _deliver = Signal(object)

    def __init__(self):
        super().__init__()
        self._running = 0
        # A queued signal is how a Python thread gets a callable onto the GUI thread.
        self._deliver.connect(lambda job: job())

    busy = Property(bool, lambda self: self._running > 0, notify=busyChanged)

    def run(self, job, then, fallback=None):
        """`job()` on a thread, then `then(result)` on the GUI thread; a failure is reported and runs `fallback()`."""
        self._running += 1
        self.busyChanged.emit()

        def work():
            try:
                result = job()
            except GoogleError as error:
                message = str(error)
                self._deliver.emit(lambda: self._finish(lambda: self._fail(message, fallback)))
                return
            except Exception as error:  # noqa: BLE001 - a thread boundary: report any bug instead of hanging busy
                traceback.print_exc()
                message = "Interner Fehler: %s" % error
                self._deliver.emit(lambda: self._finish(lambda: self._fail(message, fallback)))
                return
            self._deliver.emit(lambda: self._finish(lambda: then(result)))
        threading.Thread(target=work, daemon=True).start()

    def _finish(self, job):
        self._running -= 1
        self.busyChanged.emit()
        job()

    def _fail(self, message, fallback):
        self.failed.emit(message)
        if fallback:
            fallback()
