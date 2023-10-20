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
    session: TSession,
    initialization_behavior: SessionInitializationBehavior = SessionInitializationBehavior.AUTO,
    can_emulate: bool = True,
) -> ContextManager[TSession]:
    """Create a context manager that closes the session.

    Args:
        session: A driver session.

        initialization_behavior: Specifies whether to initialize a new
            session or attach to an existing session.

        can_emulate: Specify True, if MeasurementLink must emulate the
            INITIALIZE_SERVER_SESSION_THEN_DETACH and
            ATTACH_TO_SERVER_SESSION_THEN_CLOSE behavior. Else, False.

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

    if not can_emulate or initialization_behavior in _EXISTING_BEHAVIORS:
        if not isinstance(session, contextlib.AbstractContextManager):
            raise TypeError("Session must be a context manager.")
        return session

    if initialization_behavior == SessionInitializationBehavior.INITIALIZE_SESSION_NO_CLOSE:
        return contextlib.nullcontext(session)
    return contextlib.closing(session)
