""" Console exit helper methods."""
# fmt: off
import os
from typing import Callable

if os.name == "nt":
    import win32api
# fmt: on


def setup_unregister_on_console_close(close_service_func: Callable[[], None]) -> None:
    """Register the Callable to the SetConsoleCtrlHandler.

    Args:
    ----
        close_service_func (Callable[[None], None]): Callable to be called when console is closed.

    """
    if os.name != "nt":
        return

    def _unregister_stop_service(sig, func=None):
        close_service_func()

    win32api.SetConsoleCtrlHandler(_unregister_stop_service, True)
    return None
