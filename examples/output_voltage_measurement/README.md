## Output Voltage Measurement

This is a MeasurementLink example that sources DC voltage as input to the DUT with an NI SMU and measures the DUT output with DMM using NI-VISA.

### Features

- Uses the `nidcpower` package to access NI-DCPower from Python
- Uses the open-source `PyVISA` package to access NI-VISA from Python
- Uses the open-source `PyVISA-sim` package to simulate instruments in software
- Includes InstrumentStudio and MeasurementLink UI Editor project files
- Includes a TestStand sequence showing how to configure the pin map, register
  instrument resources with the session management service, and run a measurement
  - For the sake of simplicity, the TestStand sequence handles pin map and session
    registration and unregistration in the `Setup` and `Cleanup` sections of the main 
    sequence. For **Test UUTs** and batch process model use cases, these steps should
    be moved to the `ProcessSetup` and `ProcessCleanup` callbacks.
- Pin-aware, supporting one session and pin per instrument and a single site
  - Sources the DC voltage level of the DUT input pin
  - Measures the voltage of the DUT output pin
- Includes InstrumentStudio and MeasurementLink UI Editor project files
- For NI-DCPower, uses the NI gRPC Device Server to allow sharing the instrument sessions with other measurement services.

### Required Driver Software

- NI-DCPower
- NI-488.2 and/or NI-Serial
- NI-VISA
- Optional: NI Instrument Simulator software

Note: there is no Python instrument driver for the NI Instrument Simulator, so
this example directly performs low-level, device-specific commands and queries.

### Required Hardware

By default, this example does not require hardware; it uses a simulated instrument and PyVISA-sim to simulate NI-DCPower and NI-VISA DMM instruments in software. [`NIInstrumentSimulatorV2_0.yaml`](./NIInstrumentSimulatorV2_0.yaml) defines the behavior of the simulated NI-VISA DMM instrument.

This example requires an NI SMU that is supported by NI-DCPower (e.g. PXIe-4141).

By default, this example uses simulated instruments. To use physical instruments, edit
`_constants.py` to specify `USE_SIMULATION = False`.

To use NI Instrument Simulator hardware:

- Connect the NI Instrument Simulator over GPIB or serial.
- By default, the pin map included with this example uses the resource name
  `GPIB0::3::INSTR`, which matches the NI Instrument Simulator's factory default
  settings when connected via GPIB.
  - If this doesn't match your configuration, edit
    [`OutputVoltageMeasurement.pinmap`](./OutputVoltageMeasurement.pinmap) and replace
    `GPIB0::3::INSTR` with the desired resource name (e.g. `ASRL1::INSTR`).
  - To modify the NI Instrument Simulator configuration (e.g. GPIB address,
    serial configuration), use the `Instrument Simulator Wizard` included with
    the NI Instrument Simulator software.

To use a 3rd party DMM, such as a Keysight 34401A:
  - Verify the driver specific commands in `_visa_helpers.py` and update them if required.