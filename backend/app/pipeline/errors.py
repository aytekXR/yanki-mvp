"""Pipeline error type."""

from __future__ import annotations


class PipelineError(Exception):
    """Raised when a pipeline step fails in an expected, user-visible way.

    The worker turns this into a ``failed`` analysis with a clear ``error``
    message (rather than a raw stack trace).
    """
