#!/usr/bin/env python3
"""
Run-only state for an in-progress organize run.

Holds the minimal mutable flags an organize run needs (stop request,
in-progress flag, processed count). Source, destination, templates, and
operation mode all flow from :mod:`settings` into :mod:`organize_plan`;
they are no longer duplicated here.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class RunState:
    """Mutable flags tracking a single organize/preview run."""

    is_running: bool = False
    stop_requested: bool = False
    files_processed: int = 0

    def begin(self) -> None:
        """Reset flags at the start of a run."""
        self.is_running = True
        self.stop_requested = False
        self.files_processed = 0

    def stop(self) -> None:
        """Request that the current run stop at the next file boundary."""
        self.stop_requested = True
