"""Utilizes command line args to create a measurement client using template files."""

from typing import Sequence, Tuple

import click
from ni_measurement_plugin_sdk_service.discovery import DiscoveryClient
from ni_measurement_plugin_sdk_service.measurement.info import ServiceInfo


_V2_MEASUREMENT_SERVICE_INTERFACE = "ni.measurementlink.measurement.v2.MeasurementService"


def _get_module_name_and_service_class(
    available_services: Sequence[ServiceInfo],
) -> Tuple[str, str]:
    print("List of registered measurements: ")
    for i, service in enumerate(available_services):
        print(f"{i+1}. {service.display_name}")

    try:
        index = int(
            input("\nEnter the serial number for the desired measurement plugin client creation: ")
        )
    except Exception:
        raise Exception("Invalid input. Please try again by entering a valid serial number.")

    if index <= 0 or index > len(available_services):
        raise Exception("Input out of bounds. Please try again by entering a valid serial number.")

    measurement_service_class = available_services[index - 1].service_class
    module_name = input("Enter the name for the Python measurement plugin client module: ")
    return (module_name, measurement_service_class)


@click.command()
@click.argument("module_name", type=str, default="")
@click.option(
    "-i",
    "--interactive-mode",
    is_flag=True,
    help="Utilize interactive input for Python measurement client creation.",
)
def create_client(module_name: str, interactive_mode: bool) -> None:
    """Generates a Python measurement client module for a measurement service from the template.

    You can use the generated module to interact with the corresponding measurement service.

    MODULE_NAME: Name for the Python measurement client module to be generated.
    """
    discovery_client = DiscoveryClient()
    available_services = discovery_client.enumerate_services(_V2_MEASUREMENT_SERVICE_INTERFACE)

    if not available_services:
        print("Could find any active measurements. Please start one and try again.")
        return

    if interactive_mode:
        module_name, measurement_service_class = _get_module_name_and_service_class(
            available_services
        )
