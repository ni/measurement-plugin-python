## NI-Digital SPI

This is a MeasurementLink example that tests an SPI device using an NI Digital Pattern instrument.

### Features

- Uses the `nidigital` package to access the NI-Digital Pattern Driver from Python
- Pin-aware, supporting one session, multiple pins, and multiple selected sites
- Includes project files for Digital Pattern Editor, InstrumentStudio, MeasurementLink UI Editor
- Includes a TestStand sequence showing how to configure the pin map, register
  instrument sessions with the session management service, pre-load files into the NI-Digital
  Pattern Driver, and run a measurement
- Uses the NI gRPC Device Server to allow sharing instrument sessions with other
  measurement services when running measurements from TestStand

### Required Driver Software

- NI-Digital Pattern Driver

### Required Hardware

This example requires an NI Digital Pattern instrument (e.g. PXIe-6570).