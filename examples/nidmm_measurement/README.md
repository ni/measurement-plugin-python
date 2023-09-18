## NI-DMM Measurement

This is a MeasurementLink example that performs a measurement using an NI DMM.

### Features

- Uses the `nidmm` package to access NI-DMM from Python
- Pin-aware, supporting one session, one pin, and one selected site
- Includes InstrumentStudio and MeasurementLink UI Editor project files
- Includes a TestStand sequence showing how to configure the pin map, register
  instrument sessions with the session management service, and run a measurement
  - For the sake of simplicity, the TestStand sequence handles pin map and session
    registration and unregistration in the `Setup` and `Cleanup` sections of the main 
    sequence. For **Test UUTs** and batch process model use cases, these steps should
    be moved to the `ProcessSetup` and `ProcessCleanup` callbacks.
- Uses the NI gRPC Device Server to allow sharing instrument sessions with other
  measurement services when running measurements from TestStand

### Required Driver Software

- NI-DMM

### Required Hardware

This example requires an NI DMM (e.g. PXIe-4081).

By default, this example uses a simulated instrument. To use a physical instrument, edit
`_constants.py` to specify `USE_SIMULATION = False`.

### Tests

This example demonstrates how to write integration and unit tests for a measurement
service.

To run the tests, run:
```
poetry run python -m pytest -v
```

> **Note**
> 
> `poetry run pytest` currently does not work because it doesn't add the current directory to
> the path.

The integration tests exercise the entire service, including its interaction with the
MeasurementLink session management service, pin map services, and the NI gRPC Device
Server. This requires MeasurementLink and NI-DMM to be installed.

To regenerate the protobuf and gRPC codegen for the integration tests, run:

```
poetry run python -m grpc_tools.protoc -I tests/assets --python_out=tests/assets \
    --mypy_out=tests/assets --grpc_python_out=tests/assets --mypy_grpc_out=tests/assets \
    nidmm_measurement_parameters.proto
```