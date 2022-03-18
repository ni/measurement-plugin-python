import win32api


def setup_unregister_on_console_close(close_service_func):
    def _unregister_stop_service(sig, func=None):
        close_service_func()

    win32api.SetConsoleCtrlHandler(_unregister_stop_service, True)
