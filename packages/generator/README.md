# Measurement Plug-In SDK Generator for Python

- [Measurement Plug-In SDK Generator for Python](#measurement-plug-in-sdk-generator-for-python)
  - [Introduction](#introduction)
  - [Dependencies](#dependencies)
  - [Developing Measurements: Quick Start](#developing-measurements-quick-start)
  - [Generating Measurement Clients: Quick Start](#generating-measurement-clients-quick-start)
    - [Installation](#installation)
    - [Generating a Minimal Python Measurement Client](#generating-a-minimal-python-measurement-client)
  - [Steps to Run/Debug the Measurement Client](#steps-to-rundebug-the-measurement-client)

---

## Introduction

Measurement Plug-In SDK Generator for Python (`ni-measurement-plugin-sdk-generator`) is a Python package containing tools for generating reusable measurement plug-ins and clients.

- `ni-measurement-plugin-generator` is a command for generating measurement plug-ins using gRPC services.
- `ni-measurement-plugin-client-generator` is a command for generating plug-in clients to interact with the measurement plug-ins.

---

## Dependencies

- [Python >= 3.9](https://www.python.org/downloads/release/python-3913/)
- [mako >= 1.2.1, < 2.x](https://pypi.org/project/Mako/1.2.1/)
- [click >= 8.1.3](https://pypi.org/project/click/8.1.3/)

---

## Developing Measurements: Quick Start

For installation and usage, see [Measurement Plug-In SDK Service for Python - Developing Measurements: Quick Start](https://pypi.org/project/ni_measurement_plugin_sdk_service/#developing-measurements-quick-start) section.

---

## Generating Measurement Clients: Quick Start

This section provides instructions to generate custom measurement clients in Python using Measurement Plug-In SDK for Python.

### Installation

Make sure the system has the recommended Python version installed. Install Measurement Plug-In SDK for Python using [pip](https://pip.pypa.io/).

``` cmd
REM Activate the required virtual environment if any.
pip install ni-measurement-plugin-sdk
```

Check if you have installed the expected version of Measurement Plug-In SDK for Python installed by running the below command:

```cmd
pip show ni-measurement-plugin-sdk
```

### Generating a Minimal Python Measurement Client

Run the `ni-measurement-plugin-client-generator` tool.

1. To create measurement clients for specific measurements, use this command with optional arguments:

    ```ni-measurement-plugin-client-generator --measurement-service-class "ni.examples.SampleMeasurement_Python" [--module-name "sample_measurement_client"]  [--class-name "SampleMeasurementClient"] [--directory-out <new_path_for_created_files>]```

    - `--measurement-service-class` specifies the measurement service class for which the client is being generated.

    - Optional arguments:
        - `--module-name` and `--class-name` define the module and class names of the generated client. If not specified, they are derived from the measurement service class name.

        - `--directory-out` specifies the output directory for the generated files. If not specified, files are placed in the current directory.
        
    > **Note**: When generating multiple measurement clients, `--module-name` and `--class-name` are ignored and derived from the service class of each measurement. So, ensure that the measurement service class name adheres to proper naming conventions.

2. To create measurement clients for all registered measurements, use this command:

    `ni-measurement-plugin-client-generator --all [--directory-out <new_path_for_created_files>]`

3. To interactively create measurement clients for any registered measurements, use this command:

    `ni-measurement-plugin-client-generator --interactive`

The generated client includes four APIs: `measure`, `stream_measure`, `register_pin_map`, and `cancel`. The usage of these APIs is discussed in the ["Steps to Run/Debug the Measurement Client"](#steps-to-rundebug-the-measurement-client) section.

> **Note**:
> - The Measurement Plug-In Client is compatible with all datatypes supported by the Measurement Plug-In.
> - The Double XY datatype is not supported for measurement configurations (inputs).
> - For Enum datatypes, the generated enum class names will be the measurement parameter name suffixed with 'Enum'. For instance, if the measurement parameter name is 'Enum In', the generated enum in the client will be `EnumInEnum'.
> - Ring control in LabVIEW measurements will be represented as numeric datatypes in the generated client.

---

## Steps to Run/Debug the Measurement Client

1. Make sure the required measurement service is running before interacting with it via the client.

2. Use the client APIs from the ["Generating a Minimal Python Measurement Client"](#generating-a-minimal-python-measurement-client) section.

    1. For non-streaming measurements, use the `measure` method.

        ``` python
        from sample_measurement_client import SampleMeasurementClient
        
        client = SampleMeasurementClient()
        outputs = client.measure()
        print(outputs)
        ```

    2. For streaming measurements, use the `stream_measure` method.

        ``` python
        from sample_measurement_client import SampleMeasurementClient
        
        client = SampleMeasurementClient()
        outputs_itr = client.stream_measure()
        for index, outputs in enumerate(outputs_itr):
            print(f"outputs[{index}] = {outputs}")
        ```

    3. If a measurement requires a pin map, it can be registered using the `register_pin_map` method. By default, `sites` is set to [0].

        ``` python
        from sample_measurement_client import SampleMeasurementClient
        
        client = SampleMeasurementClient()
        client.register_pin_map(pin_map_path)
        outputs = client.measure()
        print(outputs)
        ```
        - Alternatively, when calling a measurement service from another measurement, you can pass the first measurement's pin map context to the second measurement's pin map context through the `pin_map_context` property. Sites can also be provided through the `sites` property.

        ``` python
        from sample_measurement_client import SampleMeasurementClient
        
        client = SampleMeasurementClient()
        client.pin_map_context = available_pin_map_context
        client.sites = [0, 1]
        outputs = client.measure()
        print(outputs)
        ```

    4. Cancel an ongoing `measure` or `stream_measure` call using the `cancel` method.

        ``` python
        from concurrent.futures import ThreadPoolExecutor
        from sample_measurement_client import SampleMeasurementClient
        
        client = SampleMeasurementClient()
        with ThreadPoolExecutor() as executor:
            future = executor.submit(client.measure)
            client.cancel()
            outputs = future.result()  # Raises grpc.RpcException with status code "CANCELLED" 
        ```

---
