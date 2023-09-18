import measurement
import nidmm
import pytest
from google.protobuf import any_pb2

from ni_measurementlink_service._internal.stubs.ni.measurementlink.measurement.v2.measurement_service_pb2 import (
    MeasureRequest,
)
from ni_measurementlink_service._internal.stubs.ni.measurementlink.measurement.v2.measurement_service_pb2_grpc import (
    MeasurementServiceStub,
)
from ni_measurementlink_service._internal.stubs.ni.measurementlink.pin_map_context_pb2 import (
    PinMapContext,
)
from tests.assets.nidmm_measurement_parameters_pb2 import Configurations, Outputs


def test___measurement_service___measure___returns_outputs(
    measurement_stub: MeasurementServiceStub, pin_map_id: str
) -> None:
    configurations = Configurations(
        pin_name="Pin1",
        measurement_type=nidmm.Function.DC_VOLTS.value,
        range=10.0,
        resolution_digits=5.5,
    )
    request = MeasureRequest(
        configuration_parameters=any_pb2.Any(
            type_url="ignored", value=configurations.SerializeToString()
        ),
        pin_map_context=PinMapContext(pin_map_id=pin_map_id, sites=[0]),
    )

    response_iterator = measurement_stub.Measure(request)

    responses = list(response_iterator)
    assert len(responses) == 1
    outputs = Outputs.FromString(responses[0].outputs.value)
    assert -10.0 <= outputs.measured_value <= 10.0
    assert not outputs.signal_out_of_range
    assert outputs.absolute_resolution == pytest.approx(5e-5)
