from unittest.mock import Mock

from ni_measurementlink_service import _drivers
from ni_measurementlink_service._drivers import closing_session
from tests.utilities import fake_driver


def test___driver_module___construct_grpc_session_options___sets_fields(grpc_channel: Mock) -> None:
    # The helper function tests type-checking.
    def construct_grpc_session_options(
        driver_module: _drivers.DriverModule,
    ) -> _drivers.GrpcSessionOptions:
        return driver_module.GrpcSessionOptions(
            grpc_channel,
            "MySession",
            initialization_behavior=driver_module.SessionInitializationBehavior.INITIALIZE_SERVER_SESSION,
        )

    options = construct_grpc_session_options(fake_driver)

    assert options.grpc_channel is grpc_channel
    assert options.session_name == "MySession"
    assert (
        options.initialization_behavior
        == fake_driver.SessionInitializationBehavior.INITIALIZE_SERVER_SESSION
    )


def test___closable_session___with_closing_session___session_closed() -> None:
    with closing_session(fake_driver.ClosableSession("Dev1")) as session:
        assert isinstance(session, fake_driver.ClosableSession)
        assert not session.is_closed

    assert session.is_closed


def test___context_manager_session___with_closing_session___session_closed() -> None:
    with closing_session(fake_driver.ContextManagerSession("Dev1")) as session:
        assert isinstance(session, fake_driver.ContextManagerSession)
        assert not session.is_closed

    assert session.is_closed


def test___session___with_closing_session___session_closed() -> None:
    with closing_session(fake_driver.Session("Dev1")) as session:
        assert isinstance(session, fake_driver.Session)
        assert not session.is_closed

    assert session.is_closed
