
import pathlib
from typing import Any, Dict, List, Tuple

import click
import grpc
from google.protobuf.type_pb2 import Field

from mako.template import Template

from ni_measurementlink_service._internal.parameter.metadata import ParameterMetadata

from ni_measurementlink_service._internal.stubs.ni.measurementlink.measurement.v2 import (
    measurement_service_pb2 as v2_measurement_service_pb2,
    measurement_service_pb2_grpc as v2_measurement_service_pb2_grpc,
)
from ni_measurementlink_service._internal.parameter.serializer import deserialize_parameters
from ni_measurementlink_service.discovery import DiscoveryClient

MEASUREMENT_SERVICE_INTERFACE = "ni.measurementlink.measurement.v2.MeasurementService"
_PROTODATATYPE_TO_PYTYPE_LOOKUP = {
    Field.Kind.TYPE_ENUM: int,
    Field.Kind.TYPE_INT32: int,
    Field.Kind.TYPE_INT64: int,
    Field.Kind.TYPE_UINT32: int,
    Field.Kind.TYPE_UINT64: int,
    Field.Kind.TYPE_FIXED32: int,
    Field.Kind.TYPE_FIXED64: int,
    Field.Kind.TYPE_FLOAT: float,
    Field.Kind.TYPE_DOUBLE: float,
    Field.Kind.TYPE_BOOL: bool,
    Field.Kind.TYPE_STRING: str,
}


def _check_measurement_service(
    ctx: click.Context, param: click.Parameter, service_class: str
) -> str:
    try:
        DiscoveryClient().resolve_service(
            MEASUREMENT_SERVICE_INTERFACE, service_class
        )
        return service_class
    except Exception as e:
        raise click.BadParameter(f"Error while resolving the measurement service with service class: {service_class}.")


def _get_measurement_stub(
    discovery_client: DiscoveryClient,
    service_class: str,
) -> v2_measurement_service_pb2_grpc.MeasurementServiceStub:
    resolved_service = discovery_client.resolve_service(
        MEASUREMENT_SERVICE_INTERFACE, service_class
    )
    channel = grpc.insecure_channel(resolved_service.insecure_address)
    return v2_measurement_service_pb2_grpc.MeasurementServiceStub(channel)


def _deserialize_configuration_parameters(
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


def _deserialize_output_parameters(
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


def _render_template(template_name: str, **template_args: Any) -> bytes:
    file_path = str(pathlib.Path(__file__).parent / "templates" / template_name)

    template = Template(filename=file_path, input_encoding="utf-8", output_encoding="utf-8")
    try:
        return template.render(**template_args)
    except Exception as e:
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


@click.command()
@click.argument("package_name")
@click.option(
    "-m",
    "--measurement-service-class",
    callback=_check_measurement_service,
    help="The service class of your measurement.",
)
def create_client(package_name: str, measurement_service_class: str) -> None:
    """Creates a Python measurement client for the measurement service class.

    Args:
        package_name: Name of the measurement client package.
        measurement_service_class: Measurement service class name.

    Raises:
        Exception: If the type of the configuration or output parameter couldn't be found.
    """
    discovery_client = DiscoveryClient()
    stub = _get_measurement_stub(discovery_client, measurement_service_class)
    metadata = stub.GetMetadata(v2_measurement_service_pb2.GetMetadataRequest())
    configuration_metadata_by_id, default_values = _deserialize_configuration_parameters(metadata)
    output_metadata_by_id = _deserialize_output_parameters(metadata)

    method_params_with_type = list()
    param_names = list()
    for i in range(configuration_metadata_by_id.__len__()):
        param_name = configuration_metadata_by_id[i+1].display_name.lower()
        if not param_name.isidentifier():
            if param_name.__contains__(' '):
                param_name = param_name.replace(' ', '_')
            else:
                param_name = param_name + "1"
        param_type = ""
        py_type = _PROTODATATYPE_TO_PYTYPE_LOOKUP.get(configuration_metadata_by_id[i+1].type)
        if py_type is None:
            raise Exception(
                f"Data type information not found '{configuration_metadata_by_id[i+1].type}'"
            )

        if (configuration_metadata_by_id[i+1].repeated):
            param_type=f"List[{py_type.__name__}]"
        else:
            param_type= py_type.__name__

        param_names.append(param_name)
        default_value = default_values[i]
        if isinstance(default_value, str):
            default_value = f"'{default_value}'"
        method_params_with_type.append(f"{param_name}: {param_type} = {default_value}")

    method_signature = ',\n\t'.join(method_params_with_type)
    params = ',\n\t\t'.join(param_names)

    output_list = list()
    for i in range(output_metadata_by_id.__len__()):
        param_type = ""
        py_type = _PROTODATATYPE_TO_PYTYPE_LOOKUP.get(output_metadata_by_id[i+1].type)
        if py_type is None:
            raise Exception(
                f"Data type information not found '{configuration_metadata_by_id[i+1].type}'"
            )

        if (output_metadata_by_id[i+1].repeated):
            param_type = f"List[{py_type.__name__}]"
        else:
            param_type = py_type.__name__
        output_list.append(param_type)

    ret_types = ', '.join(output_list)

    directory_out_path = pathlib.Path.cwd() / package_name
    directory_out_path.mkdir(exist_ok=True, parents=True)

    _create_file(
        "measurement_client.py.mako",
        f"{package_name}.py",
        directory_out_path,
        configuration_metadata=configuration_metadata_by_id,
        output_metadata=output_metadata_by_id,
        service_class=measurement_service_class,
        method_signature=method_signature, params=params,
        return_types=ret_types,
    )
