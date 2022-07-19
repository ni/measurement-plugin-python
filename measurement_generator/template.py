import pathlib
import re
import unittest
import uuid

import click
from mako import exceptions
from mako.template import Template


def _render_template(template_name: str, **template_args):
    try:
        template = Template(filename=str(pathlib.Path(__file__).parent / template_name))
        return template.render(**template_args)
    except:  # noqa: E722
        print(exceptions.text_error_template().render())


def _read_file(file_name):
    file_path = (
        pathlib.Path(__file__).parent.absolute()
        / f"example_renders/{file_name}"
    )
    with file_path.open("r") as fout:
        return fout.read()


class TestRender(unittest.TestCase):
    def test_py_render(self):
        self.assertEqual(
            _render_template(
                "templates/pyTemplate.txt.mako",
                display_name="SampleMeasurement",
                version="1.0.0",
                measurement_type="Sample",
                product_type="Sample",
                ui_file="measurementUI.measui",
                service_class="SampleMeasurement_Python",
                service_id="{E0095551-CB4B-4352-B65B-4280973694B2}",
                description="description",
            ),
            _read_file("example_py.txt"),
        )

    def test_sc_render(self):
        self.assertEqual(
            _render_template(
                "templates/scTemplate.txt.mako",
                display_name="SampleMeasurement",
                service_class="SampleMeasurement_Python",
                service_id="{E0095551-CB4B-4352-B65B-4280973694B2}",
                description="description",
            ),
            _read_file("example_serviceconfig.txt"),
        )


def _create_file(template_name: str, file_name: str, **template_args) -> str:
    output_file = pathlib.Path(__file__).parent / file_name

    output = _render_template(template_name, **template_args)

    with output_file.open("w") as fout:
        fout.write(output)


def _create_bat(name):
    output_file = pathlib.Path(__file__).parent / f"run_{name}.bat"

    py_file_path = (pathlib.Path(__file__).parent / f"{name}.py").resolve()

    with output_file.open("w") as fout:
        fout.write(f"call python {py_file_path}")


def _check_version(ctx, param, version):
    pattern = r"^[0-9]+\.[0-9]+\.[0-9]+$"  # ex: 2.6.8
    if re.match(pattern, version):
        return version
    raise ValueError("version not entered correctly")


def _check_ui(ctx, param, ui_file):
    if ui_file != "" and not pathlib.Path.exists(
        pathlib.Path(__file__).parent.absolute() / ui_file
    ):
        raise ValueError("can't find UI file")
    return ui_file


def _create_service_class(service_class, display_name):
    if service_class == "":
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
    if service_id == "":
        return "{" + str(uuid.uuid4()) + "}"
    else:
        service_id = service_id.replace("{", "").replace("}", "")
        if _check_uuid(service_id):
            return "{" + service_id + "}"
        raise ValueError("GUID not entered correctly")


# Takes in command line arguments to create a .py file, a .serviceConfig file, and a .bat file.
@click.command()
@click.argument("display_name")
@click.argument("version", callback=_check_version)
@click.argument("measurement_type")
@click.argument("product_type")
@click.option(
    "-U",
    "--ui-file",
    default="",
    help="Name of the UI File",
    callback=_check_ui,
)
@click.option(
    "-S",
    "--service-class",
    default="",
    help="Service Class that the measurement belongs to",
)
@click.option(
    "-I",
    "--service-id",
    default="",
    help="Unique GUID",
    callback=_check_guid,
)
@click.option(
    "-D",
    "--description",
    default="",
    help="Description URL that contains information about the measurement",
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
):
    service_class = _create_service_class(service_class, display_name)

    _create_file(
        "templates/pyTemplate.txt.mako",
        f"{display_name}.py",
        display_name=display_name,
        version=version,
        measurement_type=measurement_type,
        product_type=measurement_type,
        ui_file=ui_file,
        service_class=service_class,
        service_id=service_id,
        description=description,
    )
    _create_file(
        "templates/scTemplate.txt.mako",
        f"{display_name}.serviceConfig",
        display_name=display_name,
        service_class=service_class,
        service_id=service_id,
        description=description,
    )
    _create_bat(display_name)


def main():
    _create_measurement()


if __name__ == "__main__":
    main()
