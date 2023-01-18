## NI-VISA DMM Measurement

This is a MeasurementLink example that performs a DMM measurement using NI-VISA
and an NI Instrument Simulator v2.0. 

### Features

- Uses the open-source `PyVISA` package to access NI-VISA from Python
- Uses the open-source `PyVISA-sim` package to simulate instruments in software
- Pin-aware, supporting a custom instrument type and a single session/pin/site
- Includes InstrumentStudio and MeasurementLink UI Editor project files
- Includes a TestStand sequence
- Uses the MeasurementLink session management service
- Does not use the NI gRPC Device Server

### Required Driver Software

- NI-488.2 and/or NI-Serial
- NI-VISA
- Optional: NI Instrument Simulator software

Note: there is no Python instrument driver for the NI Instrument Simulator, so
this example directly performs low-level, device-specific commands and queries.

### Required Hardware

By default, this example does not require hardware; it uses PyVISA-sim to
simulate the instrument in software.
[`NIInstrumentSimulatorV2_0.yaml`](./NIInstrumentSimulatorV2_0.yaml) defines the
behavior of the simulated instrument. 

To use NI Instrument Simulator hardware:
- Disable software simulation by setting `USE_SIMULATION = False` in both
  [`measurement.py`](./measurement.py) and
  [`teststand_fixture.py`](./teststand_fixture.py). 
- Connect the NI Instrument Simulator over GPIB or serial.
- By default, the pin map included with this example uses the resource name
  `GPIB0::3::INSTR`, which matches the NI Instrument Simulator's factory default
  settings when connected via GPIB.
  - If this doesn't match your configuration, edit
    [`NIVisaDmmMeasurement.pinmap`](./NIVisaDmmMeasurement.pinmap) and replace
    `GPIB0::3::INSTR` with the desired resource name (e.g. `ASRL1::INSTR`).
  - To modify the NI Instrument Simulator configuration (e.g. GPIB address,
    serial configuration), use the `Instrument Simulator Wizard` included with
    the NI Instrument Simulator software.

