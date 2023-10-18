"""Shared code for interfacing with driver APIs."""
from __future__ import annotations

import contextlib
from typing import ContextManager, TypeVar, cast

from ni_measurementlink_service.session_management._types import SessionInitializationBehavior

TSession = TypeVar("TSession")


def closing_session(
    session: TSession,
    initialization_behavior: SessionInitializationBehavior = SessionInitializationBehavior.AUTO,
) -> ContextManager[TSession]:
    """Create a context manager that closes the session.

    Args:
        session: A driver session.

    Returns:
        A context manager that yields the session and closes it.
    """
    if initialization_behavior == SessionInitializationBehavior.AUTO:
        # yield the session's context manager.
        return cast(ContextManager[TSession], session)
    elif (
        initialization_behavior
        == SessionInitializationBehavior.INITIALIZE_SERVER_SESSION_THEN_DETACH
        or initialization_behavior == SessionInitializationBehavior.ATTACH_TO_SERVER_SESSION
    ):
        return contextlib.nullcontext(session)
    elif hasattr(session, "close"):
        return contextlib.closing(session)
    else:
        raise TypeError(
            f"Invalid session type '{type(session)}'. A session must be a context manager and/or "
            "have a close() method."
        )
