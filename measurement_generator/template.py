import click
import re
import uuid
import os.path
from mako.template import Template


def create_py(name, vers, m_type, p_type, ui, s_class, id, desc):
    py = open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), f"{name}.py"), "w"
    )

    template = Template(
        filename=os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "pyTemplate.txt"
        )
    )
    py.write(
        template.render(
            display_name=name,
            version=vers,
            measurement_type=m_type,
            product_type=p_type,
            ui_file=ui,
            service_class=s_class,
            service_id=id,
            description=desc,
        )
    )
    py.close()


def create_serviceConfig(name, s_class, id, desc):
    sc = open(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)), f"{name}.serviceConfig"), "w"
    )

    template = Template(
        filename=os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "scTemplate.txt"
        )
    )
    sc.write(
        template.render(
            display_name=name, service_class=s_class, service_id=id, description=desc
        )
    )
    sc.close()


def create_bat(name):
    bat = open(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), f"run{name}.bat"), "w"
    )
    py_file_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), f"{name}.py"
    )
    bat.write(f"call python {py_file_path}")
    bat.close()


def check_version(version):
    pattern = "^[0-9]+\.[0-9]+\.[0-9]+$"
    if not re.search(pattern, version):
        raise ValueError("version not entered correctly")


def check_ui(ui_file):
    if ui_file != "" and not os.path.exists(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), ui_file)
    ):
        raise ValueError("can't find UI file")


def create_service_class(service_class, display_name):
    if service_class == "":
        return f"{display_name}_Python"
    else:
        return service_class


def check_uuid4(test_uuid, version=4):
    try:
        return uuid.UUID(test_uuid).version == version
    except ValueError:
        return False


def create_guid(service_id):
    if service_id == "":
        return "{" + str(uuid.uuid4()) + "}"
    else:
        service_id = service_id.replace("{", "").replace("}", "")
        if check_uuid4(service_id):
            return "{" + service_id + "}"
        raise ValueError("GUID not entered correctly")


# Takes in command line arguments to create a .py file, a .serviceConfig file, and a .bat file.
@click.command()
@click.argument("display_name")
@click.argument("version")
@click.argument("measurement_type")
@click.argument("product_type")
@click.option(
    "-UI", 
    "--ui_file", 
    default="", 
    help="Name of the UI File")
@click.option(
    "-SC",
    "--service_class",
    default="",
    help="Service Class that the measurement belongs to",
)
@click.option(
    "-ID", 
    "--service_id", 
    default="", 
    help="Unique GUID")
@click.option(
    "-DE",
    "--description",
    default="",
    help="Description URL that contains information about the measurement",
)
def create_template(
    display_name,
    version,
    measurement_type,
    product_type,
    ui_file,
    service_class,
    service_id,
    description,
):
    check_version(version)
    check_ui(ui_file)
    service_class = create_service_class(service_class, display_name)
    service_id = create_guid(service_id)

    create_py(
        display_name,
        version,
        measurement_type,
        product_type,
        ui_file,
        service_class,
        service_id,
        description,
    )
    create_serviceConfig(display_name, service_class, service_id, description)
    create_bat(display_name)


if __name__ == "__main__":
    create_template()
