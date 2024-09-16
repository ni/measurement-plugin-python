import pytest

from ni_measurement_plugin_sdk_service.grpc.channelpool import GrpcChannelPool


@pytest.mark.parametrize(
    "target,expected_result",
    [
        ("127.0.0.1", False),  # Port must be specified explicitly
        ("[::1]", False),  # Port must be specified explicitly
        ("localhost", False),  # Port must be specified explicitly
        ("127.0.0.1:100", True),
        ("[::1]:100", True),
        ("localhost:100", True),
        ("http://127.0.0.1", False),  # Port must be specified explicitly
        ("http://[::1]", False),  # Port must be specified explicitly
        ("http://localhost", False),  # Port must be specified explicitly
        ("http://127.0.0.1:100", True),
        ("http://[::1]:100", True),
        ("http://localhost:100", True),
        ("1.1.1.1:100", False),
        ("http://www.google.com:80", False),
    ],
)
def test___channel_pool___is_local___returns_expected_result(
    target: str, expected_result: bool
) -> None:
    channel_pool = GrpcChannelPool()

    result = channel_pool._is_local(target)

    assert result == expected_result
