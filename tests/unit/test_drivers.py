from ni_measurementlink_service._drivers import closing_session
from ni_measurementlink_service.session_management._types import SessionInitializationBehavior
from tests.utilities import fake_driver


def test___closable_session___with_closing_session___session_closed() -> None:
    with closing_session(
        fake_driver.ClosableSession("Dev1"),
        SessionInitializationBehavior.INITIALIZE_SERVER_SESSION,
    ) as session:
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
