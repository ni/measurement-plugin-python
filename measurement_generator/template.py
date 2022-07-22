"""Utilizes command line args to create a measurement using template files."""
import pathlib
import re
import uuid

import click
from mako import exceptions
from mako.template import Template


def _render_template(template_name: str, **template_args) -> str:
    file_path = str(pathlib.Path(__file__).parent / "templates" / template_name)
    template = Template(filename=file_path)
    try:
        return template.render(**template_args)
    except:  # noqa: E722
        print(exceptions.text_error_template().render())


def _create_file(
    template_name: str, file_name: str, directory_out, **template_args
) -> str:
    output_file = pathlib.Path(directory_out) / file_name

    output = _render_template(template_name, **template_args)

    with output_file.open("w") as fout:
        fout.write(output)


def _create_bat(name, directory_out):
    output_file = pathlib.Path(directory_out) / f"start.bat"

    py_file_path = (pathlib.Path(directory_out) / f"{name}.py").resolve()

    with output_file.open("w") as fout:
        fout.write(f"call python {py_file_path}")


def _check_version(ctx, param, version):
    pattern = r"^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$"
    if re.match(pattern, version):
        return version
    raise ValueError("version not entered correctly")


def _check_ui(ctx, param, ui_file):
    if ui_file != "" and not pathlib.Path.exists(
        pathlib.Path(__file__).parent.absolute() / ui_file
    ):
        raise ValueError("can't find UI file")
    return ui_file


def _check_ui_type(ui_file):
    ext = pathlib.Path(ui_file).suffix
    if ext == ".measui":
        return "MeasurementUI"
    elif ext == ".vi":
        return "LabVIEW"
    else:
        raise ValueError(
            "UI file extension does not match possible UI file types. Should be .measui or .vi."
        )


def _assess_service_class(service_class, display_name):
    if service_class is None:
        return f"{display_name}_Python"
    else:
        return service_class


def _check_uuid(test_uuid):
    try:
        uuid.UUID(test_uuid)
        return True
    except ValueError:
        return False


def _check_guid(ctx, param, service_id):
    if service_id is None:
        return "{" + str(uuid.uuid4()) + "}"
    else:
        service_id = service_id.replace("{", "").replace("}", "")
        if _check_uuid(service_id):
            return "{" + service_id + "}"
        raise ValueError("GUID not entered correctly")


@click.command()
@click.argument("display_name")
@click.argument("version", callback=_check_version)
@click.argument("measurement_type")
@click.argument("product_type")
@click.option(
    "-u",
    "--ui-file",
    default="measurementUI.measui",
    help="Name of the UI File",
    callback=_check_ui,
)
@click.option(
    "-s",
    "--service-class",
    help="Service Class that the measurement belongs to. Default is <display_name>_Python",
)
@click.option(
    "-i",
    "--service-id",
    help="Unique GUID",
    callback=_check_guid,
)
@click.option(
    "-d",
    "--description",
    help="Description URL that contains information about the measurement",
)
@click.option(
    "-o",
    "--directory-out",
    default=pathlib.Path(__file__).parent,
    help="Output directory for measurement files",
)
def _create_measurement(
    display_name,
    version,
    measurement_type,
    product_type,
    ui_file,
    service_class,
    service_id,
    description,
    directory_out,
):
    """Takes in command line arguments to create a .py file, a .serviceConfig file, and a .bat file.
    These files work in unison to preform a measurement, 
    although the .bat file is optional in its use.

    DISPLAY_NAME is the name of the measurement.
    The created .py file and .serviceConfig file will take this as its file name.

    VERSION is the current version of the measurement.
    Should be formatted like x.x.x.x
    EX: 0.2.6.8

    MEASUREMENT_TYPE is the type of measurement the measurement files will eventually preform.

    PRODUCT_TYPE is the type of product the measurement files will eventually produce.
    """
    service_class = _assess_service_class(service_class, display_name)
    ui_file_type = _check_ui_type(ui_file)

    _create_file(
        "pyTemplate.py.mako",
        f"{display_name}.py",
        directory_out,
        display_name=display_name,
        version=version,
        measurement_type=measurement_type,
        product_type=product_type,
        ui_file=ui_file,
        ui_file_type=ui_file_type,
        service_class=service_class,
        service_id=service_id,
        description=description,
    )
    _create_file(
        "scTemplate.serviceConfig.mako",
        f"{display_name}.serviceConfig",
        directory_out,
        display_name=display_name,
        service_class=service_class,
        service_id=service_id,
        description=description,
    )
    _create_bat(display_name, directory_out)


def main():
    _create_measurement()


if __name__ == "__main__":
    main()
