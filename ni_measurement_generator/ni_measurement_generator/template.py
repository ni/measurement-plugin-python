"""Utilizes command line args to create a measurement using template files."""
import pathlib
import re
import uuid

import click
from mako import exceptions
from mako.template import Template


def _render_template(template_name: str, **template_args) -> str:
    file_path = str(pathlib.Path(__file__).parent / "templates" / template_name)

    with open(file_path, "r") as file:
        file_contents = file.read()
    template = Template(file_contents)
    try:
        return template.render(**template_args)
    except:  # noqa: E722
        print(exceptions.text_error_template().render())


def _create_file(template_name: str, file_name: str, directory_out, **template_args) -> str:
    output_file = pathlib.Path(directory_out) / file_name

    output = _render_template(template_name, **template_args)

    with output_file.open("w") as fout:
        fout.write(output)


def _create_bat(directory_out):
    output_file = pathlib.Path(directory_out) / "start.bat"

    with output_file.open("w") as fout:
        fout.write(f"call python %~dp0measurement.py")


def _check_version(ctx, param, version):
    pattern = r"^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$"
    if re.match(pattern, version):
        return version
    raise ValueError("version not entered correctly")


def _get_ui_type(ui_file):
    ext = pathlib.Path(ui_file).suffix
    if ext == ".measui":
        return "MeasurementUI"
    elif ext == ".vi":
        return "LabVIEW"
    else:
        raise ValueError(
            "UI file extension does not match possible UI file types. Should be .measui or .vi."
        )


def _resolve_ui_file(ui_file, display_name):
    if ui_file is None:
        return f"{display_name}.measui"
    else:
        return ui_file


def _resolve_service_class(service_class, display_name):
    if service_class is None:
        return f"{display_name}_Python"
    else:
        return service_class


def _check_guid(ctx, param, service_id):
    try:
        parsed_id = uuid.uuid4() if service_id is None else uuid.UUID(service_id)
        return "{" + str(parsed_id).upper() + "}"
    except ValueError:
        raise ValueError(f"The {param} must be a valid GUID.")


@click.command()
@click.argument("display_name")
@click.option(
    "--measurement-version",
    callback=_check_version,
    help="Version number in the form x.y.z.q",
    default="1.0.0.0",
)
@click.option(
    "--measurement-type", help="Service-defined Measurement type", default="MeasurementType"
)
@click.option("--product-type", help="Service-defined Product type", default="ProductType")
@click.option(
    "-u",
    "--ui-file",
    help="Name of the UI File, Default is <display_name>.measui.",
)
@click.option(
    "-s",
    "--service-class",
    help="Service Class that the measurement belongs to. Default is <display_name>_Python.",
)
@click.option(
    "-i",
    "--service-id",
    help="Unique GUID.",
    callback=_check_guid,
)
@click.option(
    "-d",
    "--description",
    help="Description URL that contains information about the measurement.",
)
@click.option(
    "-o",
    "--directory-out",
    default=pathlib.Path(__file__).parent,
    help="Output directory for measurement files.",
)
def create_measurement(
    display_name,
    measurement_version,
    measurement_type,
    product_type,
    ui_file,
    service_class,
    service_id,
    description,
    directory_out,
):
    """Generate a Python measurement service from a template.

    You can use this to get started writing your own measurement services.

    DISPLAY_NAME: The measurement display name for client to display to user.
    The created .serviceconfig file will take this as its file name.

    VERSION: The measurement version that helps to maintain versions of a measurement in future.
    Should be formatted like x.x.x.x
    e.g. 0.2.6.8

    MEASUREMENT_TYPE: Represents category of measurement for the ProductType,
    e.g. AC or DC measurements.

    PRODUCT_TYPE: Represents type of the DUT,
    e.g. ADC, LDO.
    """
    service_class = _resolve_service_class(service_class, display_name)
    ui_file = _resolve_ui_file(ui_file, display_name)
    ui_file_type = _get_ui_type(ui_file)

    _create_file(
        "measurement.py.mako",
        "measurement.py",
        directory_out,
        display_name=display_name,
        version=measurement_version,
        measurement_type=measurement_type,
        product_type=product_type,
        ui_file=ui_file,
        ui_file_type=ui_file_type,
        service_class=service_class,
        service_id=service_id,
        description=description,
    )
    _create_file(
        "measurement.serviceconfig.mako",
        f"{display_name}.serviceconfig",
        directory_out,
        display_name=display_name,
        service_class=service_class,
        service_id=service_id,
        description=description,
        ui_file_type=ui_file_type,
    )
    if ui_file_type == "MeasurementUI":
        _create_file(
            "measurement.measui.mako",
            f"{ui_file}",
            directory_out,
            display_name=display_name,
            service_class=service_class,
        )
        _create_file(
            "measurement.measproj.mako",
            f"{display_name}.measproj",
            directory_out,
            ui_file=ui_file,
        )
    _create_bat(directory_out)
