""" Console exit helper methods."""
from typing import Callable

import win32api


def setup_unregister_on_console_close(close_service_func: Callable[[None], None]) -> None:
    """Register the Callable to the SetConsoleCtrlHandler.

    Args:
    ----
        close_service_func (Callable[[None], None]): Callable to be called when console is closed.

    """

    def _unregister_stop_service(sig, func=None):
        close_service_func()

    win32api.SetConsoleCtrlHandler(_unregister_stop_service, True)
    return None
