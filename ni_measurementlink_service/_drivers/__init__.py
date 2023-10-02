"""Shared code for interfacing with driver APIs."""
from __future__ import annotations

import contextlib
from typing import ContextManager, TypeVar

TSession = TypeVar("TSession")


def closing_session(session: TSession) -> ContextManager[TSession]:
    """Create a context manager that closes the session.

    Args:
        session: A driver session.

    Returns:
        A context manager that yields the session and closes it.
    """
    if isinstance(session, contextlib.AbstractContextManager):
        # Assume the session yields itself.
        return session
    elif hasattr(session, "close"):
        return contextlib.closing(session)
    else:
        raise TypeError(
            f"Invalid session type '{type(session)}'. A session must be a context manager and/or "
            "have a close() method."
        )
