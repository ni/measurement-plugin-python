"""Utilizes command line args to create a measurement using template files."""

import logging
import pathlib
import re
from typing import Any, Optional, Tuple

import click
from mako import exceptions
from mako.template import Template

_logger = logging.getLogger(__name__)


def _render_template(template_name: str, **template_args: Any) -> bytes:
    file_path = str(pathlib.Path(__file__).parent / "templates" / template_name)

    template = Template(filename=file_path, input_encoding="utf-8", output_encoding="utf-8")
    try:
        return template.render(**template_args)
    except Exception as e:
        _logger.error(exceptions.text_error_template().render())
        raise click.ClickException(
            f'An error occurred while rendering template "{template_name}".'
        ) from e


def _create_file(
    template_name: str, file_name: str, directory_out: pathlib.Path, **template_args: Any
) -> None:
    output_file = directory_out / file_name

    output = _render_template(template_name, **template_args)

    with output_file.open("wb") as fout:
        fout.write(output)


def _check_version(ctx: click.Context, param: click.Parameter, version: str) -> str:
    pattern = r"^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$"
    if re.match(pattern, version):
        return version
    raise click.BadParameter(f"Invalid version '{version}'.")


def _check_ui_file(
    ctx: click.Context, param: click.Parameter, ui_file: Optional[str]
) -> Optional[str]:
    if ui_file is not None:
        _ = _get_ui_type(ui_file)
    return ui_file


def _get_ui_type(ui_file: str) -> str:
    ext = pathlib.Path(ui_file).suffix
    if ext == ".measui":
        return "MeasurementUI"
    elif ext == ".vi":
        return "LabVIEW"
    else:
        raise click.BadParameter(
            f"Unsupported extension '{ext}'. Supported extensions: '.measui', '.vi'"
        )


def _resolve_ui_file(ui_file: Optional[str], display_name_for_filenames: str) -> str:
    if ui_file is None:
        return f"{display_name_for_filenames}.measui"
    else:
        return ui_file


def _resolve_service_class(service_class: str, display_name: str) -> str:
    if service_class is None:
        return f"{display_name}_Python"
    else:
        return service_class


@click.command()
@click.argument("display_name")
@click.option(
    "--measurement-version",
    callback=_check_version,
    help="Version number in the form 'x.y.z.q'. Default: '1.0.0.0'",
    default="1.0.0.0",
)
@click.option(
    "-u",
    "--ui-file",
    callback=_check_ui_file,
    help="Name of the UI File. Default: '<display_name>.measui'",
)
@click.option(
    "-s",
    "--service-class",
    help="Service Class that the measurement belongs to. Default: '<display_name>_Python'",
)
@click.option(
    "-D",
    "--description",
    default="",
    help="Short description of the measurement",
)
@click.option(
    "-d",
    "--description-url",
    default="",
    help="Description URL that links to a web page containing information about the measurement.",
)
@click.option(
    "-o",
    "--directory-out",
    help="Output directory for measurement files. Default: '<current_directory>/<display_name>'",
)
@click.option(
    "-c",
    "--collection",
    default="",
    help="\b\nThe collection that this measurement belongs to. Collection names are specified"
    "using a period-delimited namespace hierarchy and are case-insensitive."
    "\nExample: 'CurrentTests.Inrush'",
)
@click.option(
    "-t",
    "--tags",
    default=[],
    multiple=True,
    help="\b\nTags describing the measurement. This option may be repeated to specify multiple tags. Tags are case-insensitive."
    "\nExample: '-t test -t Internal'",
)
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Enable verbose logging. Repeat to increase verbosity.",
)
def create_measurement(
    display_name: str,
    measurement_version: str,
    ui_file: Optional[str],
    service_class: str,
    description_url: str,
    directory_out: Optional[str],
    description: str,
    collection: str,
    tags: Tuple[str, ...],
    verbose: bool,
) -> None:
    """Generate a Python measurement service from a template.

    You can use this to get started writing your own MeasurementLink services.

    DISPLAY_NAME: The measurement display name for client to display to user.
    The created .serviceconfig file will take this as its file name.
    """
    if verbose > 1:
        level = logging.DEBUG
    elif verbose == 1:
        level = logging.INFO
    else:
        level = logging.WARNING
    logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=level)

    service_class = _resolve_service_class(service_class, display_name)
    display_name_for_filenames = re.sub(r"\s+", "", display_name)
    ui_file = _resolve_ui_file(ui_file, display_name_for_filenames)
    ui_file_type = _get_ui_type(ui_file)
    serviceconfig_file = f"{display_name_for_filenames}.serviceconfig"
    if directory_out is None:
        directory_out_path = pathlib.Path.cwd() / display_name_for_filenames
    else:
        directory_out_path = pathlib.Path(directory_out)

    directory_out_path.mkdir(exist_ok=True, parents=True)

    _create_file(
        "measurement.py.mako",
        "measurement.py",
        directory_out_path,
        display_name=display_name,
        version=measurement_version,
        ui_file=ui_file,
        ui_file_type=ui_file_type,
        service_class=service_class,
        description_url=description_url,
        serviceconfig_file=serviceconfig_file,
    )
    _create_file(
        "measurement.serviceconfig.mako",
        serviceconfig_file,
        directory_out_path,
        display_name=display_name,
        service_class=service_class,
        description_url=description_url,
        ui_file_type=ui_file_type,
        description=description,
        collection=collection,
        tags=list(tags),
    )
    if ui_file_type == "MeasurementUI":
        _create_file(
            "measurement.measui.mako",
            ui_file,
            directory_out_path,
            display_name=display_name,
            service_class=service_class,
        )
        _create_file(
            "measurement.measproj.mako",
            f"{display_name_for_filenames}.measproj",
            directory_out_path,
            ui_file=ui_file,
        )
    _create_file("start.bat.mako", "start.bat", directory_out_path)
    _create_file("_helpers.py.mako", "_helpers.py", directory_out_path)
