"""TestStand code module for setting up pin maps with MeasurementLink."""
from typing import Any

from _helpers import GrpcChannelPoolHelper, PinMapClient, TestStandSupport


def update_pin_map(pin_map_path: str, sequence_context: Any) -> str:
    """Update registered pin map contents.

    Create and register a pin map if a pin map resource for the specified pin map id is not found.

    Args:
        pin_map_path: An absolute or relative path to the pin map file.
        sequence_context: The SequenceContext COM object from the TestStand sequence execution.
            (Dynamically typed.)
    """
    teststand_support = TestStandSupport(sequence_context)
    pin_map_abs_path = teststand_support.resolve_file_path(pin_map_path)

    with GrpcChannelPoolHelper() as grpc_channel_pool:
        pin_map_client = PinMapClient(grpc_channel=grpc_channel_pool.pin_map_channel)
        pin_map_id = pin_map_client.update_pin_map(pin_map_abs_path)

    teststand_support.set_active_pin_map_id(pin_map_id)
    return pin_map_id
