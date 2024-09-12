"""Creates a measurement client through use of __init__.py."""

import click

from ni_measurement_plugin_sdk_generator.client import (
    create_client_in_batch_mode,
    create_client_in_interactive_mode,
)


@click.command()
@click.argument("mode", default="b")
@click.pass_context
def _create_client(context: click.Context, mode: str) -> None:
    if mode == "i":
        context.invoke(create_client_in_interactive_mode)
    else:
        context.invoke(create_client_in_batch_mode())


_create_client()
