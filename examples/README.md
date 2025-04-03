
## Example Measurements

These are example measurements for use with InstrumentStudio 2025 Q2 or later.

For best results, use the example measurements corresponding to the version of InstrumentStudio
that you are using. Newer examples may demonstrate features that are not available in older
versions of InstrumentStudio.

| InstrumentStudio Version | Release | Download |
| ------------------------ | -------- | ------- |
| 2025 Q2                  | [2.3.0](https://github.com/ni/measurement-plugin-python/releases/tag/2.3.0) | [measurement-plugin-python-examples-2.3.0.zip](https://github.com/ni/measurement-plugin-python/releases/download/2.3.0/measurement-plugin-python-examples-2.3.0.zip) |
| 2025 Q1                  | [2.2.0](https://github.com/ni/measurement-plugin-python/releases/tag/2.2.0) | [measurement-plugin-python-examples-2.2.0.zip](https://github.com/ni/measurement-plugin-python/releases/download/2.2.0/measurement-plugin-python-examples-2.2.0.zip) |
| 2024 Q4                  | [2.1.0](https://github.com/ni/measurement-plugin-python/releases/tag/2.1.0) | [measurement-plugin-python-examples-2.1.0.zip](https://github.com/ni/measurement-plugin-python/releases/download/2.1.0/measurement-plugin-python-examples-2.1.0.zip) |
| 2024 Q3                  | [2.0.0](https://github.com/ni/measurement-plugin-python/releases/tag/2.0.0) | [measurement-plugin-python-examples-2.0.0.zip](https://github.com/ni/measurement-plugin-python/releases/download/2.0.0/measurement-plugin-python-examples-2.0.0.zip) |
| 2024 Q2                  | [1.4.0](https://github.com/ni/measurement-plugin-python/releases/tag/1.4.0) | [measurementlink-python-examples-1.4.0.zip](https://github.com/ni/measurement-plugin-python/releases/download/1.4.0/measurementlink-python-examples-1.4.0.zip) |
| Older versions | | See [releases](https://github.com/ni/measurement-plugin-python/releases) page |

The TestStand sequence files associated with each example are saved in TestStand 2021 SP1.

### Available Example Measurements

- Instrument-specific
  - `nidaqmx_analog_input`: Performs a finite analog input measurement with NI-DAQmx.
  - `nidcpower_source_dc_voltage`: Sources and measures a DC voltage with an NI SMU. Provides a Measurement UI and a LabVIEW UI.
  - `nidcpower_source_dc_voltage_with_multiplexer`: Sources and measures a DC voltage with an NI SMU via an NI-SWITCH multiplexer.
  - `nidigital_spi`: Tests an SPI device using an NI Digital Pattern instrument.
  - `nidmm_measurement`: Performs a measurement using an NI DMM.
  - `nifgen_standard_function`: Generates a standard function waveform using an NI waveform generator.
  - `niscope_acquire_waveform`: Acquires a waveform using an NI oscilloscope.
  - `niswitch_control_relays`: Controls relays using an NI relay driver (e.g. PXI-2567).
  - `nivisa_dmm_measurement`: Performs a DMM measurement using NI-VISA and an NI Instrument Simulator v2.0.
  - `output_voltage_measurement`: Sources DC voltage as input to the DUT with an NI SMU and measures the DUT output with a DMM and NI-VISA.
- Software-only (no instrument or driver needed)
  - `sample_measurement`: Performs a loopback measurement with various data types. Provides a Measurement UI and a LabVIEW UI.
  - `game_of_life`: Displays Conway's Game of Life in a graph. Shows measurement cancellation and updating the UI during a measurement.

For more details about a specific example, see the `README.md` file included with the example.

### Setting up the Example Measurements

The example measurements are *Poetry-based* projects. Follow the steps below to set up an example measurement:

1. Install `poetry`. Refer to <https://python-poetry.org/docs/#installation> for information on installing Poetry.

2. Open a command prompt and change the working directory to the directory of the example measurement you want to work with.

    ``` cmd
    cd <path_of_example_measurement>
    REM Example: cd "..\measurement-plugin-python\examples\nidcpower_source_dc_voltage"
    ```

3. Run `poetry install`. This command creates/updates the virtual environment (`.venv`) and installs the needed dependencies (including `ni-measurement-plugin-sdk-service` package) into the virtual environment.

    ``` cmd
    poetry install
    ```
    - If you get a "command not found" error during `poetry install`, make sure that you added the Poetry path to the system path. Refer to [https://python-poetry.org/docs/#installing-with-the-official-installer/Add-poetry-to-your-path](https://python-poetry.org/docs/#installing-with-the-official-installer:~:text=Add%20Poetry%20to%20your%20PATH)

### Creating Simulated Devices for Example Measurements

- To enable simulation for all the modular instrument and VISA examples, copy `.env.simulation` to `.env` in the `examples` directory.

### Executing the Example Measurements

1. Start the discovery service if not already started.
2. Use `poetry run` to run the measurement service:

    ``` cmd
    poetry run python measurement.py
    ```

### Static Registration of Example Measurements

To statically register an example measurement service with the NI Discovery Service, do the following:

1. Copy the example measurement's directory (including the `.serviceconfig` file and startup batch file) to a subdirectory of `C:\ProgramData\National Instruments\Plug-Ins\Measurements`.
> **Note**
> Do not copy the `.venv` subdirectory&mdash;the virtual environment must be re-created in the new location.
2. Create a virtual environment in the new location by opening a command prompt to the new example directory under `C:\ProgramData` and running `poetry install`.

    ``` cmd
    cd <path_of_example_measurement>
    REM Example: cd "C:\ProgramData\National Instruments\Plug-Ins\Measurements\dc_measurement"
    poetry install
    ```

Once the example measurement service is statically registered, the NI Discovery Service makes it visible in supported NI applications.

> **Note**
> To set up and statically register all of the example measurements, run [`install_examples.py`](../scripts/install_examples.py).
