from collections.abc import Generator
from ipaddress import ip_address

import psutil
import pytest

from ni_measurement_plugin_sdk_service.measurement.service import MeasurementService
from tests.utilities.discovery_service_process import DiscoveryServiceProcess
from tests.utilities.measurements import loopback_measurement


def test___loopback_measurement___listening_on_loopback_interface(
    measurement_service: MeasurementService,
):
    insecure_port = int(measurement_service.service_location.insecure_port)

    listener_ips = [
        ip_address(conn.laddr.ip)
        for conn in psutil.Process().net_connections()
        if conn.laddr.port == insecure_port and conn.status == psutil.CONN_LISTEN
    ]
    assert len(listener_ips) >= 1 and all([ip.is_loopback for ip in listener_ips])
    assert measurement_service.service_location.ssl_authenticated_port == ""


@pytest.fixture(scope="module")
def measurement_service(
    discovery_service_process: DiscoveryServiceProcess,
) -> Generator[MeasurementService, None, None]:
    """Test fixture that creates and hosts a measurement service."""
    with loopback_measurement.measurement_service.host_service() as service:
        yield service
