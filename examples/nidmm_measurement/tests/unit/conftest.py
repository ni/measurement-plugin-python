"""Unit test fixtures for NI-DMM measurements."""
from unittest.mock import Mock

import measurement
import nidmm
import pytest
from pytest_mock import MockerFixture

from ni_measurementlink_service.measurement.service import MeasurementContext
from ni_measurementlink_service.session_management import (
    Client,
    SingleSessionReservation,
)


@pytest.fixture
def measurement_context(mocker: MockerFixture) -> Mock:
    """Test fixture that creates a mock MeasurementContext."""
    measurement_context = mocker.create_autospec(MeasurementContext)
    mocker.patch.object(measurement.measurement_service, "context", measurement_context)
    return measurement_context


@pytest.fixture
def session_management_client(mocker: MockerFixture) -> Mock:
    """Test fixture that creates a mock SessionManagementClient."""
    session_management_client = mocker.create_autospec(Client)
    mocker.patch(
        "measurement.create_session_management_client", return_value=session_management_client
    )
    return session_management_client


@pytest.fixture
def nidmm_session(mocker: MockerFixture) -> Mock:
    """Test fixture that creates a mock nidmm.Session."""
    session = mocker.create_autospec(nidmm.Session)
    mocker.patch("measurement.create_session", return_value=session)
    session.__enter__.return_value = session
    return session


@pytest.fixture
def single_session_reservation(mocker: MockerFixture, session_management_client: Mock) -> Mock:
    """Test fixture that creates a mock SingleSessionReservation."""
    single_session_reservation = mocker.create_autospec(SingleSessionReservation)
    session_management_client.reserve_session.return_value = single_session_reservation
    return single_session_reservation
