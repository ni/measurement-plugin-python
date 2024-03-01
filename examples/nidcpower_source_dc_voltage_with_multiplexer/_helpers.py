"""Helper classes and functions for MeasurementLink examples."""

import logging
import pathlib
from typing import Any, Callable, TypeVar

import click


class TestStandSupport(object):
    """Class that communicates with TestStand."""

    def __init__(self, sequence_context: Any) -> None:
        """Initialize the TestStandSupport object.

        Args:
            sequence_context:
                The SequenceContext COM object from the TestStand sequence execution.
                (Dynamically typed.)
        """
        self._sequence_context = sequence_context

    def get_active_pin_map_id(self) -> str:
        """Get the active pin map id from the NI.MeasurementLink.PinMapId runtime variable.

        Returns:
            The resource id of the pin map that is registered to the pin map service.
        """
        return self._sequence_context.Execution.RunTimeVariables.GetValString(
            "NI.MeasurementLink.PinMapId", 0x0
        )

    def resolve_file_path(self, file_path: str) -> str:
        """Resolve the absolute path to a file using the TestStand search directories.

        Args:
            file_path:
                An absolute or relative path to the file. If this is a relative path, this function
                searches the TestStand search directories for it.

        Returns:
            The absolute path to the file.
        """
        if pathlib.Path(file_path).is_absolute():
            return file_path
        (_, absolute_path, _, _, user_canceled) = self._sequence_context.Engine.FindFileEx(
            fileToFind=file_path,
            absolutePath=None,
            srchDirType=None,
            searchDirectoryIndex=None,
            userCancelled=None,  # Must match spelling used by TestStand
            searchContext=self._sequence_context.SequenceFile,
        )
        if user_canceled:
            raise RuntimeError("File lookup canceled by user.")
        return absolute_path


def configure_logging(verbosity: int) -> None:
    """Configure logging for this process."""
    if verbosity > 1:
        level = logging.DEBUG
    elif verbosity == 1:
        level = logging.INFO
    else:
        level = logging.WARNING
    logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=level)


F = TypeVar("F", bound=Callable)


def verbosity_option(func: F) -> F:
    """Decorator for --verbose command line option."""
    return click.option(
        "-v",
        "--verbose",
        "verbosity",
        count=True,
        help="Enable verbose logging. Repeat to increase verbosity.",
    )(func)
