"""Test fixtures for unit tests."""

from unittest.mock import Mock

import grpc
import pytest
from pytest_mock import MockerFixture

from ni_measurementlink_service._channelpool import GrpcChannelPool
from ni_measurementlink_service._internal.discovery_client import DiscoveryClient


@pytest.fixture
def discovery_client(mocker: MockerFixture) -> Mock:
    """Test fixture that creates a mock DiscoveryClient."""
    return mocker.create_autospec(DiscoveryClient)


@pytest.fixture
def grpc_channel(mocker: MockerFixture) -> Mock:
    """Test fixture that creates a mock grpc.Channel."""
    return mocker.create_autospec(grpc.Channel)


@pytest.fixture
def grpc_channel_pool(mocker: MockerFixture) -> Mock:
    """Test fixture that creates a mock GrpcChannelPool."""
    return mocker.create_autospec(GrpcChannelPool)
