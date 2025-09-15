"""Workspace file monitoring utilities."""

from __future__ import annotations

import fnmatch
import logging
import threading
from pathlib import Path
from typing import Optional, Sequence

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from core.event_recorder import EventRecorder

logger = logging.getLogger(__name__)

# Default patterns to ignore for the workspace watcher. These cover common temporary
# and cache files that would create noise in the event stream.
DEFAULT_IGNORE_PATTERNS: Sequence[str] = (
    "__pycache__/*",
    "*.pyc",
    "*.pyo",
    "*.tmp",
    "*.swp",
    "*.DS_Store",
)


class _WorkspaceFileChangeHandler(FileSystemEventHandler):
    """Watchdog handler that forwards file events to the EventRecorder."""

    def __init__(
        self,
        event_recorder: EventRecorder,
        workspace_path: Path,
        ignore_patterns: Sequence[str] = (),
    ) -> None:
        super().__init__()
        self._event_recorder = event_recorder
        self._workspace_path = Path(workspace_path)
        self._ignore_patterns = tuple(ignore_patterns)

    def on_created(self, event) -> None:  # type: ignore[override]
        if event.is_directory:
            return
        self._record_change(Path(event.src_path), "created")

    def on_modified(self, event) -> None:  # type: ignore[override]
        if event.is_directory:
            return
        self._record_change(Path(event.src_path), "modified")

    def on_deleted(self, event) -> None:  # type: ignore[override]
        if event.is_directory:
            return
        self._record_change(Path(event.src_path), "deleted")

    def on_moved(self, event) -> None:  # type: ignore[override]
        if event.is_directory:
            return
        # Record as delete + create to reflect the move in the event stream.
        self._record_change(Path(event.src_path), "deleted")
        self._record_change(Path(event.dest_path), "created")

    def _record_change(self, path: Path, change_type: str) -> None:
        relative_path = self._make_relative_path(path)
        if self._should_ignore(relative_path):
            return

        try:
            self._event_recorder.append_file_change(relative_path, change_type)
            logger.debug("Recorded workspace change: %s (%s)", relative_path, change_type)
        except Exception as exc:  # pragma: no cover - logging only
            logger.error(
                "Failed to record workspace change for %s: %s", relative_path, exc
            )

    def _make_relative_path(self, path: Path) -> str:
        try:
            relative = path.relative_to(self._workspace_path)
        except ValueError:
            relative = path
        return relative.as_posix()

    def _should_ignore(self, relative_path: str) -> bool:
        return any(fnmatch.fnmatch(relative_path, pattern) for pattern in self._ignore_patterns)


class WorkspaceFileMonitor:
    """Monitor the workspace directory and record file changes."""

    def __init__(
        self,
        workspace_path: Path,
        event_recorder: EventRecorder,
        *,
        recursive: bool = True,
        ignore_patterns: Optional[Sequence[str]] = None,
    ) -> None:
        self._workspace_path = Path(workspace_path)
        self._event_recorder = event_recorder
        self._recursive = recursive
        patterns = tuple(ignore_patterns) if ignore_patterns is not None else DEFAULT_IGNORE_PATTERNS
        self._ignore_patterns: Sequence[str] = patterns

        self._observer: Optional[Observer] = None
        self._handler: Optional[_WorkspaceFileChangeHandler] = None
        self._lock = threading.Lock()
        self._running = False

    def start(self) -> None:
        """Start the watchdog observer in a background thread."""
        with self._lock:
            if self._running:
                logger.debug("Workspace file monitor already running")
                return

            if self._event_recorder is None:
                raise ValueError("EventRecorder is required to start the file monitor")

            self._workspace_path.mkdir(parents=True, exist_ok=True)

            handler = _WorkspaceFileChangeHandler(
                self._event_recorder, self._workspace_path, self._ignore_patterns
            )
            observer = Observer()
            observer.schedule(handler, str(self._workspace_path), recursive=self._recursive)
            observer.daemon = True
            observer.start()

            self._observer = observer
            self._handler = handler
            self._running = True

            logger.info("Started workspace file monitor on %s", self._workspace_path)

    def stop(self) -> None:
        """Stop the watchdog observer and wait for the thread to finish."""
        observer: Optional[Observer] = None
        with self._lock:
            if not self._running or self._observer is None:
                return

            observer = self._observer
            observer.stop()

        if observer is not None:
            observer.join(timeout=5)

        with self._lock:
            self._observer = None
            self._handler = None
            self._running = False

            logger.info("Stopped workspace file monitor")

    @property
    def is_running(self) -> bool:
        with self._lock:
            return self._running


__all__ = ["WorkspaceFileMonitor"]
