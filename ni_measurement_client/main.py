"""Python measurement client."""

from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import grpc
from google.protobuf import any_pb2
from grpc import Channel
from ni_measurementlink_service._internal.parameter.metadata import ParameterMetadata
from ni_measurementlink_service._internal.parameter.serializer import (
    deserialize_parameters,
    serialize_parameters,
)
from ni_measurementlink_service._internal.stubs.ni.measurementlink.measurement.v2 import (
    measurement_service_pb2 as v2_measurement_service_pb2,
    measurement_service_pb2_grpc as v2_measurement_service_pb2_grpc,
)
from ni_measurementlink_service._internal.stubs.ni.measurementlink.pin_map_context_pb2 import (
    PinMapContext,
)
from ni_measurementlink_service.discovery import DiscoveryClient, ServiceDescriptor
from ni_measurementlink_service.pin_map import PinMapClient

MEASUREMENT_SERVICE_INTERFACE = "ni.measurementlink.measurement.v2.MeasurementService"

# NOTE: Ensure that the below file path is updated before starting the application.
PIN_MAP_PATH = r"D:\Odyssey\measurementlink-python\examples\nidcpower_source_dc_voltage\NIDCPowerSourceDCVoltage.pinmap"
SITES = [0]


def display_and_get_available_measurement_services(
    discovery_client: DiscoveryClient,
) -> Optional[Sequence[ServiceDescriptor]]:
    available_services = discovery_client.enumerate_services(MEASUREMENT_SERVICE_INTERFACE)

    if len(available_services) == 0:
        print("No measurement services are running.")
        return None

    print("Available services:")
    for i, services in enumerate(available_services):
        print(f"{i+1}. {services.display_name}")

    print("-------------------------------------------------------------------------------")
    print("Press Ctrl + C to stop the application!\n")
    return available_services


def get_insecure_grpc_channel_for(discovery_client: DiscoveryClient, service_class: str) -> Channel:
    resolved_service = discovery_client.resolve_service(
        MEASUREMENT_SERVICE_INTERFACE, service_class
    )
    return grpc.insecure_channel(resolved_service.insecure_address)


def get_measurement_service_stub(
    discovery_client: DiscoveryClient,
) -> Optional[v2_measurement_service_pb2_grpc.MeasurementServiceStub]:
    available_services = display_and_get_available_measurement_services(discovery_client)
    if not available_services:
        return None

    selected_measurement_index = get_measurement_selection()
    if selected_measurement_index == -1:
        return None
    
    channel = get_insecure_grpc_channel_for(
        discovery_client, available_services[selected_measurement_index - 1].service_class
    )

    return v2_measurement_service_pb2_grpc.MeasurementServiceStub(channel)


def deserialize_configuration_parameters(
    metadata: v2_measurement_service_pb2.GetMetadataResponse,
) -> Tuple[Dict[int, ParameterMetadata], List[Any]]:
    configuration_metadata_by_id = {}
    for configuration in metadata.measurement_signature.configuration_parameters:
        configuration_metadata_by_id[configuration.field_number] = ParameterMetadata(
            configuration.name,
            configuration.type,
            configuration.repeated,
            0,
            configuration.annotations,
            configuration.message_type,
        )

    params = deserialize_parameters(
        configuration_metadata_by_id, metadata.measurement_signature.configuration_defaults.value
    )
    values = [None] * params.__len__()
    for k, v in params.items():
        configuration_metadata_by_id[k] = configuration_metadata_by_id[k]._replace(default_value=v)
        values[k - 1] = v

    return (configuration_metadata_by_id, values)


def deserialize_output_parameters(
    metadata: v2_measurement_service_pb2.GetMetadataResponse,
) -> Dict[int, ParameterMetadata]:
    output_metadata_by_id = {}
    for output in metadata.measurement_signature.outputs:
        output_metadata_by_id[output.field_number] = ParameterMetadata(
            output.name,
            output.type,
            output.repeated,
            0,
            output.annotations,
            output.message_type,
        )

    return output_metadata_by_id


def get_measure_request(
    configuration_metadata: Dict[int, ParameterMetadata], values: Sequence[Any]
):
    serialized_configuration = any_pb2.Any(
        value=serialize_parameters(configuration_metadata, values)
    )
    return v2_measurement_service_pb2.MeasureRequest(
        configuration_parameters=serialized_configuration,
        pin_map_context=PinMapContext(
            pin_map_id=pin_map_path,
            sites=SITES,
        ),
    )


def get_measurement_selection() -> int:
    try:
        return int(input("Select a measurement service to run: "))
    except ValueError:
        print("WARN: Invalid input! Going ahead with the first measurement.")
        return 1
    except KeyboardInterrupt:
        return -1


def get_active_pin_map() -> str:
    print("\nNote: Site '0' will be used for the measurement execution.")
    try:
        path = input("Provide the pin map file's absolute path (without quotes): ")
    except KeyboardInterrupt:
        return ""

    if not Path.is_file(Path(path)):
        print(f"WARN: Couldn't find the file. Going ahead with the default pin map file: {PIN_MAP_PATH}")
        path = PIN_MAP_PATH

    return path


if __name__ == "__main__":
    discovery_client = DiscoveryClient()
    pin_map_client = PinMapClient(discovery_client=discovery_client)

    while True:
        print("\n-------------------------------------------------------------------------------")
        measurement_service_stub = get_measurement_service_stub(discovery_client)
        if measurement_service_stub:
            metadata = measurement_service_stub.GetMetadata(
                v2_measurement_service_pb2.GetMetadataRequest()
            )

            configuration_metadata_by_id, default_values = deserialize_configuration_parameters(metadata)
            output_metadata_by_id = deserialize_output_parameters(metadata)

            print("\nDefault input values:")
            for k, _ in configuration_metadata_by_id.items():
                print(f"{configuration_metadata_by_id[k].display_name}: {default_values[k-1]}")

            pin_map_path = get_active_pin_map()
            if pin_map_path == "":
                break
            
            pin_map_client.update_pin_map(pin_map_path)

            request = get_measure_request(configuration_metadata_by_id, default_values)

            print("\nMeasured values:")
            for response in measurement_service_stub.Measure(request):
                output_values = deserialize_parameters(output_metadata_by_id, response.outputs.value)
                for k, v in output_values.items():
                    print(f"{output_metadata_by_id[k].display_name}: {v}")
        else:
            print("\n\nClosing the application either because user requested or there's no active measurement.")
            break
