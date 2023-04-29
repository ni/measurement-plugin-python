"""Contains Test Doubles related to Discovery service. """
import uuid


class FakeRegistrationResponse:
    """Fake Registration Response."""

    registration_id: str


class FakeDiscoveryServiceStub:
    """Fake Registry Service Stub."""

    def RegisterService(self, request):
        """Fake gRPC registration call to discovery service."""
        self.request = request
        response = FakeRegistrationResponse()
        response.registration_id = str(uuid.uuid4())
        self.registration_done = True
        return response

    def UnregisterService(self, request):
        """Fake gRPC un-registration call to discovery service."""
        pass


class FakeDiscoveryServiceStubError(FakeDiscoveryServiceStub):
    """Fake Registry Service Stub that throws error to mimic unavailability of discovery service."""

    def RegisterService(self, request):
        """Fake gRPC registration call to discovery service."""
        raise Exception("TestException")

    def UnregisterService(self, request):
        """Fake gRPC un-registration call to discovery service."""
        raise Exception("TestException")
