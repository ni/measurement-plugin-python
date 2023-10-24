"""Shared code for interfacing with driver APIs."""
from __future__ import annotations

import contextlib
from typing import ContextManager, TypeVar

from ni_measurementlink_service.session_management._types import SessionInitializationBehavior

TSession = TypeVar("TSession")

_EXISTING_BEHAVIORS = [
    SessionInitializationBehavior.AUTO,
    SessionInitializationBehavior.ATTACH_TO_SERVER_SESSION,
    SessionInitializationBehavior.INITIALIZE_SERVER_SESSION,
]


def closing_session(
    initialization_behavior: SessionInitializationBehavior,
    session: TSession,
) -> ContextManager[TSession]:
    """Create a context manager that closes the session.

    Args:
        initialization_behavior: Specifies whether to initialize a new
            session or attach to an existing session.

        session: A driver session.

    Returns:
        A context manager that yields the session and closes it.

    Raises:
        TypeError: If the session is not a context manager and if it does not have a close() method.

        ValueError: If the initialization behavior is invalid.
    """
    if not hasattr(session, "close"):
        raise TypeError("Session must have a close() method.")
    elif initialization_behavior not in SessionInitializationBehavior:
        raise ValueError(f"Invalid initialization behavior: '{initialization_behavior}'.")

    if initialization_behavior in _EXISTING_BEHAVIORS:
        if not isinstance(session, contextlib.AbstractContextManager):
            raise TypeError("Session must be a context manager.")
        return session

    if initialization_behavior == SessionInitializationBehavior.INITIALIZE_SESSION_THEN_DETACH:
        return contextlib.nullcontext(session)
    return contextlib.closing(session)
