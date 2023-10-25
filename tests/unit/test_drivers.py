import pytest

from ni_measurementlink_service._drivers import closing_session_with_ts_code_module_support
from tests.utilities import fake_driver
from tests.utilities.fake_driver import SessionInitializationBehavior


@pytest.mark.parametrize(
    "initialization_behavior",
    [
        (SessionInitializationBehavior.AUTO),
        (SessionInitializationBehavior.INITIALIZE_SERVER_SESSION),
        (SessionInitializationBehavior.ATTACH_TO_SESSION_THEN_CLOSE),
    ],
)
def test___closable_context_manager_session___with_closing_session_with_ts_code_module_support___session_closed(
    initialization_behavior: SessionInitializationBehavior,
) -> None:
    with closing_session_with_ts_code_module_support(
        initialization_behavior, fake_driver.Session("Dev1", initialization_behavior)
    ) as session:
        assert isinstance(session, fake_driver.Session)
        assert not session.is_closed

    assert session.is_closed


@pytest.mark.parametrize(
    "initialization_behavior",
    [
        (SessionInitializationBehavior.ATTACH_TO_SERVER_SESSION),
        (SessionInitializationBehavior.INITIALIZE_SESSION_THEN_DETACH),
    ],
)
def test___closable_context_manager_session___with_closing_session_with_ts_code_module_support___session_detached(
    initialization_behavior: SessionInitializationBehavior,
) -> None:
    with closing_session_with_ts_code_module_support(
        initialization_behavior, fake_driver.Session("Dev1", initialization_behavior)
    ) as session:
        assert isinstance(session, fake_driver.Session)
        assert not session.is_closed

    assert not session.is_closed


@pytest.mark.parametrize(
    "initialization_behavior",
    [
        (SessionInitializationBehavior.AUTO),
        (SessionInitializationBehavior.INITIALIZE_SERVER_SESSION),
        (SessionInitializationBehavior.ATTACH_TO_SERVER_SESSION),
        (SessionInitializationBehavior.ATTACH_TO_SESSION_THEN_CLOSE),
        (SessionInitializationBehavior.INITIALIZE_SESSION_THEN_DETACH),
    ],
)
def test___context_manager_session___with_closing_session_with_ts_code_module_support___raises_type_error(
    initialization_behavior: SessionInitializationBehavior,
) -> None:
    with pytest.raises(TypeError) as exc_info:
        with closing_session_with_ts_code_module_support(
            initialization_behavior,
            fake_driver.ContextManagerSession("Dev1", initialization_behavior),
        ):
            pass

    assert "Session must have a close() method." in exc_info.value.args[0]


@pytest.mark.parametrize(
    "initialization_behavior",
    [
        (SessionInitializationBehavior.AUTO),
        (SessionInitializationBehavior.INITIALIZE_SERVER_SESSION),
        (SessionInitializationBehavior.ATTACH_TO_SERVER_SESSION),
    ],
)
def test___closable_session___with_closing_session_with_ts_code_module_support___raises_type_error(
    initialization_behavior: SessionInitializationBehavior,
) -> None:
    with pytest.raises(TypeError) as exc_info:
        with closing_session_with_ts_code_module_support(
            initialization_behavior, fake_driver.ClosableSession("Dev1", initialization_behavior)
        ):
            pass

    assert "Session must be a context manager." in exc_info.value.args[0]
