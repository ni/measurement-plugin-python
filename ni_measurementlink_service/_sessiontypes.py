"""Session management data types.

This submodule is intended to prevent circular imports between
session_management.py and driver-specific code such as
_drivers/_nidcpower.py.
"""
from enum import IntEnum


class SessionInitializationBehavior(IntEnum):
    """Specifies whether to initialize a new session or attach to an existing session."""

    AUTO = 0
    """
    The NI gRPC Device Server will attach to an existing session with the
    specified name if it exists, otherwise the server will initialize a new
    session.

    Note: When using the Session as a context manager and the context exits, the
    behavior depends on what happened when the constructor was called. If it
    resulted in a new session being initialized on the NI gRPC Device Server,
    then it will automatically close the server session. If it instead attached
    to an existing session, then it will detach from the server session and
    leave it open.
    """

    INITIALIZE_SERVER_SESSION = 1
    """
    Require the NI gRPC Device Server to initialize a new session with the
    specified name.

    Note: When using the Session as a context manager and the context exits, it
    will automatically close the server session.
    """

    ATTACH_TO_SERVER_SESSION = 2
    """
    Require the NI gRPC Device Server to attach to an existing session with the
    specified name.

    Note: When using the Session as a context manager and the context exits, it
    will detach from the server session and leave it open.
    """
