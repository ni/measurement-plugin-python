"""
@generated by mypy-protobuf.  Do not edit manually!
isort:skip_file
"""
import builtins
import google.protobuf.descriptor
import google.protobuf.message
import typing
import typing_extensions

DESCRIPTOR: google.protobuf.descriptor.FileDescriptor = ...

class ServiceLocation(google.protobuf.message.Message):
    """Represents the location of a service.  The location is generally
    the IP address and port number.  But it can also be something
    like a UDS socket.
    """

    DESCRIPTOR: google.protobuf.descriptor.Descriptor = ...
    LOCATION_FIELD_NUMBER: builtins.int
    OPTIMAL_ROUTE_FIELD_NUMBER: builtins.int
    INSECURE_PORT_FIELD_NUMBER: builtins.int
    SSL_AUTHENTICATED_PORT_FIELD_NUMBER: builtins.int
    location: typing.Text = ...
    """location (ipaddress) of the service"""

    optimal_route: typing.Text = ...
    """optimal route (ipaddress) to use when communicating with the
    service
    This may be a link-local connection, or a high speed link that
    is available between the two communicating services
    """

    insecure_port: typing.Text = ...
    """port to use for insecure HTTP connections"""

    ssl_authenticated_port: typing.Text = ...
    """port to use for Secure SSL authenticated connections"""

    def __init__(
        self,
        *,
        location: typing.Text = ...,
        optimal_route: typing.Text = ...,
        insecure_port: typing.Text = ...,
        ssl_authenticated_port: typing.Text = ...,
    ) -> None: ...
    def ClearField(
        self,
        field_name: typing_extensions.Literal[
            "insecure_port",
            b"insecure_port",
            "location",
            b"location",
            "optimal_route",
            b"optimal_route",
            "ssl_authenticated_port",
            b"ssl_authenticated_port",
        ],
    ) -> None: ...

global___ServiceLocation = ServiceLocation
