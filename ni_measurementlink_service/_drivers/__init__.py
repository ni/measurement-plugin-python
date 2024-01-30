"""Shared code for interfacing with driver APIs."""

from __future__ import annotations

import contextlib
from typing import ContextManager, TypeVar

from ni_measurementlink_service.session_management._types import (
    SessionInitializationBehavior,
)

TSession = TypeVar("TSession")

_EXISTING_BEHAVIORS = [
    SessionInitializationBehavior.AUTO,
    SessionInitializationBehavior.ATTACH_TO_SERVER_SESSION,
    SessionInitializationBehavior.INITIALIZE_SERVER_SESSION,
]


def closing_session_with_ts_code_module_support(
    initialization_behavior: SessionInitializationBehavior,
    session: TSession,
) -> ContextManager[TSession]:
    """Create a context manager that closes the session.

    Emulates the behavior of INITIALIZE_SESSION_THEN_DETACH and ATTACH_TO_SESSION_THEN_CLOSE.
    """
    if not hasattr(session, "close"):
        raise TypeError("Session must have a close() method.")

    if initialization_behavior in _EXISTING_BEHAVIORS:
        return closing_session(session)
    elif initialization_behavior == SessionInitializationBehavior.INITIALIZE_SESSION_THEN_DETACH:
        return contextlib.nullcontext(session)
    elif initialization_behavior == SessionInitializationBehavior.ATTACH_TO_SESSION_THEN_CLOSE:
        return contextlib.closing(session)
    else:
        raise ValueError(f"Invalid initialization behavior: '{initialization_behavior}'.")


def closing_session(session: TSession) -> ContextManager[TSession]:
    """A context manager that yields the session and closes it."""
    if not isinstance(session, contextlib.AbstractContextManager):
        raise TypeError("Session must be a context manager.")
    return session
