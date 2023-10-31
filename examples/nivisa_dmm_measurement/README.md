## NI-VISA DMM Measurement

This is a MeasurementLink example that performs a DMM measurement using NI-VISA
and a DMM that supports SCPI commands.  

### Features

- Uses the open-source `PyVISA` package to access NI-VISA from Python
- Uses the open-source `PyVISA-sim` package to simulate instruments in software
- Pin-aware, supporting a custom instrument type and a single session/pin/site
- Includes InstrumentStudio and MeasurementLink UI Editor project files
- Includes a TestStand sequence showing how to configure the pin map, register
  instrument resources with the session management service, and run a measurement
  - For the sake of simplicity, the TestStand sequence handles pin map and session
    registration and unregistration in the `Setup` and `Cleanup` sections of the main 
    sequence. For **Test UUTs** and batch process model use cases, these steps should
    be moved to the `ProcessSetup` and `ProcessCleanup` callbacks.
- Demonstrates how to share instrument resources with other measurement services
  when running measurements from TestStand, without using NI gRPC Device Server

### Required Driver Software

- NI-488.2 and/or NI-Serial
- NI-VISA
- Optional: NI Instrument Simulator software

> **Note:**
>
> This example uses the custom instrument driver `_visa_dmm.py` to perform the device-specific commands and queries.

### Required Hardware

By default, this example does not require hardware; it uses PyVISA-sim to
simulate the instrument in software.
[`_visa_dmm_sim.yaml`](./_visa_dmm_sim.yaml) defines the
behavior of the simulated instrument. 

Supported instrument models:
- NI Instrument Simulator v2.0
- HP/Agilent/Keysight 34401A DMM

By default, this example uses a physical instrument or a simulated device created in NI MAX. To
automatically create a simulated device when running the measurement or TestStand sequence, follow
the steps below:
- Create a `.env` file in the measurement service's directory or one of its parent directories (such
  as the root of your Git repository or `C:\ProgramData\National
  Instruments\MeasurementLink\Services` for statically registered measurement services).
- Add the following option to the `.env` file to enable simulation via the driver's `simulate`
  parameter:

  ```
  MEASUREMENTLINK_VISA_DMM_SIMULATE=1
  ```

To use a physical instrument:
- Connect the instrument to a supported interface, such as GPIB or serial.
- By default, the pin map included with this example uses the resource name
  `GPIB0::3::INSTR`, which matches the NI Instrument Simulator's factory default
  settings when connected via GPIB.
  - If this doesn't match your instrument's configuration, edit
    [`NIVisaDmmMeasurement.pinmap`](./NIVisaDmmMeasurement.pinmap) and replace
    `GPIB0::3::INSTR` with the desired resource name (e.g. `ASRL1::INSTR`).
  - To modify the NI Instrument Simulator configuration (e.g. GPIB address,
    serial configuration), use the `Instrument Simulator Wizard` included with
    the NI Instrument Simulator software.
  - To configure third party instruments, see the documentation provided with the instrument.

### Session Management

This example has a slightly different approach to session management than the
examples for NI PXI modular instruments. 

The examples for NI PXI modular instruments use the NI gRPC Device Server to
share a single driver session between multiple operating system processes. When running
measurements outside of TestStand, each measurement re-initalizes the
instrument. When running measurements in TestStand, the `ProcessSetup` callback
initializes the instrument once per sequence execution, which avoids
the overhead of re-initializing the instrument for each measurement.

This VISA example does not use NI gRPC Device Server. The measurement logic and
TestStand code module open and close VISA driver sessions as needed in multiple
operating system processes. However, the instrument initialization behavior is
the same as before: outside of TestStand, each measurement re-initializes the
instrument; in TestStand, the `ProcessSetup` callback initalizes the instrument
once per sequence execution. This approach works for VISA because multiple
processes (TestStand, multiple measurement services) can connect to the same
instrument without resetting any instrument state.

In both cases, the `ProcessSetup` callback registers the instrument with the
session management service, the measurement logic uses the session management
service to reserve and unreserve the instrument, and the `ProcessCleanup`
callback unregisters the instrument with the session management service. This
ensures that only one measurement at a time has access to the instrument.