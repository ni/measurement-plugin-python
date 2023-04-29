## NI-FGEN Standard Function

This is a MeasurementLink example that generates a standard function waveform
using an NI waveform generator.

### Features

- Uses the `nifgen` package to access NI-FGEN from Python
- Demonstrates how to cancel a running measurement by breaking a long wait into
  multiple short waits
- Pin-aware, supporting multiple sessions, multiple pins, and multiple selected sites
  - Outputs the same waveform configuration on all selected pin/site combinations
  - Does not synchronize waveforms
- Includes InstrumentStudio and MeasurementLink UI Editor project files
- Includes a TestStand sequence showing how to configure the pin map, register
  instrument sessions with the session management service, and run a measurement
  - For the sake of simplicity, the TestStand sequence handles pin map and session registration and unregistration in the `Setup` and `Cleanup` sections of the main sequence. For **Test UUTs** and batch process model use cases, these steps should be moved to the `ProcessSetup` and `ProcessCleanup` callbacks.
- Uses the NI gRPC Device Server to allow sharing instrument sessions with other
  measurement services when running measurements from TestStand

### Required Driver Software

- NI-FGEN

### Required Hardware

This example requires an NI waveform generator (e.g. PXIe-5423 (2CH)).