# Python Measurements

## Contents

1. [Introduction](#introduction)

2. [Abbreviations](#abbreviations)

3. [Dependencies](#dependencies)

4. [Quick Start](#quick-start)

    1. [Installation](#installation)

    2. [Developing a minimal python measurement](#developing-a-minimal-python-measurement)

    3. [Steps to run a measurement service](#steps-to-run-a-measurement-service)

5. [Managing Measurement as Python Package(Project)](#managing-measurement-as-python-packageproject)
    1. [Create and Manage Python Measurement Package using poetry](#create-and-manage-python-measurement-package-using-poetry)
    2. [Create and Manage Python Measurement Package using venv](#create-and-manage-python-measurement-package-using-venv)
    3. [Create and Manage Python Measurement Package by directly installing NIMS as a system-level package](#create-and-manage-python-measurement-package-by-directly-installing-nims-as-a-system-level-package)

6. [Examples](#examples)

    1. [Setting up the Example Measurements](#setting-up-the-example-measurements)
    2. [Executing the Example Measurements](#executing-the-example-measurements)

---

## Introduction

**Measurement methodology** is a way in which certain parameters of Device Under Test (or Objects) are calculated. These parameters can be like an electrical characteristic of a Semiconductor Chip. Normally, a measurement procedure can be written in test documentation on how best a measurement can be made using the given instrumentation. If we convert the Measurement methodology from test documentation into a software program, it is called the **Measurement Code Module**. We will refer Measurement Code Module as **Measurement** in this document.

`ni_measurement_service` is a python framework that enables measurement developers to quickly create python measurements and run them as a service(gRPC)

---

## Abbreviations

- NIMS - Nationals Instrument Measurement Service Framework - `ni_measurement_service`

---

## Dependencies

- Python >= 3.8( 3.8 recommended)
- [grpcio](https://pypi.org/project/grpcio/1.41.1/) = 1.41.1
- [protobuf](https://pypi.org/project/protobuf/3.19.1/) = 3.19.1

---

## Quick Start

### Installation

Download the `ni_measurement_service.tar.gz` and install the NIMS Framework.

If using [pip](https://pip.pypa.io/).

``` cmd
REM Activate the required virtual environment if any.
pip install <path_of_ni_measurement_service-x.x.x.tar.gz>
```

If using [poetry](https://python-poetry.org/) to manage a python project.

``` cmd
REM Run the command from within the poetry project directory.
poetry add <path_of_ni_measurement_service-x.x.x.tar.gz>
```

### Developing a minimal python measurement

1. Create a python file(.py file)

2. Import `ni_measurement_service`

    ``` python
    import ni_measurement_service as nims
    ```

3. Define `measurement_info` and `service_info` with the required details.

    ``` python
    measurement_info = nims.MeasurementInfo(
        display_name="FooMeasurement", # The display name of the measurement
        version="0.1.0.0", # The version of the measurement
        measurement_type="", # The Type of the measurement.
        product_type="", # The Product Type related to the measurement.
        ui_file_path="", # Absolute file path of the UI File. Developer can relative construct the path here.
        ui_file_type="", # Type of UI File.
    )

    service_info = nims.ServiceInfo(
        service_class="FooMeasurement_Python", # Service Class that the measurement belongs to.
        service_id="<GUID>", #Unique GUID 
        description_url="", # Description URL that contains information about the measurement. Can be Empty if there is no Description URL.
    )
    ```

4. Create a new `MeasurementService` Instance.

    ``` python
    foo_measurement_service = nims.MeasurementService(measurement_info, service_info)
    ```

5. Define a python function with required measurement logic based on your required measurement methodology.
    1. The measurement function must return the outputs as a list.

    ``` python
    def measure(input_1, input_2): 
        ''' A simple Measurement method'''
        return ["foo", "bar"]
    ```

6. Register the defined python function as measurement.

    ``` python
    @foo_measurement_service.register_measurement
    def measure(input_1, input_2): 
        ''' A simple Measurement method'''
        return ["foo", "bar"]
    ```

7. Provide metadata of the measurement's configuration(input parameters) and outputs(output parameters)
    1. Use the `configuration()` decorator to provide metadata about the configurations.**The order of the configuration decorator must match with the order of the parameters defined in the function signature.**

        ``` python
        @foo_measurement_service.register_measurement
        #Display Names can not contains backslash or front slash.
        @foo_measurement_service.configuration("DisplayNameForInput1", DataType.String, "DefaultValueForInput1")
        @foo_measurement_service.configuration("DisplayNameForInput2", DataType.String, "DefaultValueForInput2")
        def measure(input_1, input_2):
            ''' A simple Measurement method'''
            return ["foo", "bar"]
        ```

    2. Use the `output()` decorator to provide metadata about the output.**The order of the output decorators from top to bottom must match the order of the values of the list returned by the function.**

        ``` python
        @foo_measurement_service.register_measurement
        @foo_measurement_service.configuration("DisplayNameForInput1", DataType.String, "DefaultValueForInput1")
        @foo_measurement_service.configuration("DisplayNameForInput2", DataType.String, "DefaultValueForInput2")
        @foo_measurement_service.output("DisplayNameForOutput1", DataType.String)
        @foo_measurement_service.output("DisplayNameForOutput2", DataType.String)
        def measure(input_1, input_2):
            return ["foo", "bar"]
        ```

8. Startup logic.
    - To start the registered measurement as service call the `host_service()` from the `MeasurementService` instance.
    - Use the `close_service()` function to properly terminate the service.
    - A typical implementation is shown below:

    ``` python
    if __name__ == "__main__":
        foo_measurement_service.host_service()
        input("To Exit during the Service lifetime, Press Enter.\n")
        foo_measurement_service.close_service()
    ```

### Steps to run a measurement service

1. Start the discovery service if not already started.

2. Activate related virtual environments. Measurement developers can skip this step if they are not using any virtual environments or poetry-based projects.

    ```cmd
    .venv\scripts\activate
    ```

    - After successful activation, you can see the name of the environment, `(.venv)` is added to the command prompt.

3. Run the measurement file created using NIMS.

4. After the usage of measurement, deactivate the virtual environment. Measurement developers can skip this step if they are not using any virtual environments or poetry-based projects.

    ```cmd
    deactivate
    ```

---

## Managing Measurement as Python Package(Project)

Measurement and its related files can be maintained as a python package. The basic Components of any Python Measurement Package are:

1. Measurement Python Module(.py file)
    - This file contains all the details related to the measurement and also contains the logic for the measurement execution.
    - This file is run to start the measurement as a service.

2. UI File
    - UI file for the Measurement. Type of Supported UI Files are:
        - Screen file(.isscr): created using the **Plugin UI Editor application**.
        - LabVIEW UI(.vi)
    - The path and type of this file is configured by `ui_file_path` and `ui_file_type` respectively in `measurement_info` variable definition in Measurement Python Module(.py file).

Python communities have different ways of managing a python package and its dependencies. It is up to the measurement developer, on how they wanted to maintain the package and dependencies. Measurement developers can choose from a few common approaches discussed below based on their requirements.
Note: Once we have the template support for Python measurement, the approach to managing the python measurement package(project) will be streamlined and simplified.

### Create and Manage Python Measurement Package using poetry

1. Setting up Poetry(One-time setup)
    1. Make sure the system has the recommended python version installed.

    2. Install `poetry` using the installation steps given in <https://python-poetry.org/docs/#installation>.

2. Create a new python project and add NIMS Framework as a dependency to the project.

    1. Open a command prompt, change the working directory to the directory of your choice where you want to create the project.

        ``` cmd
        cd <path_of_directory_of_your_choice>
        ```

    2. Create a python package(project) using the poetry new command. Poetry will create boilerplate files and folders that are commonly needed for a python project.

        ``` cmd
        poetry new <name_of_the_project>
        ```

    3. Add the `ni_measurement_service-x.x.x` framework package as a dependency.

        ``` cmd
        cd <name_of_the_project>
        poetry add <path_of_ni_measurement_service-x.x.x.tar.gz>
        ```

    4. Virtual environment will be auto-created by poetry.

    5. Create measurement modules as described in ["Developing a minimal python measurement"](#developing-a-minimal-python-measurement)
        - Any additional dependencies required by measurement can be added using add command.

            ``` cmd
            poetry add <dependency_package_name>
            ```

For detailed info on managing projects using poetry [refer to the official documentation](https://python-poetry.org/docs/cli/).

### Create and Manage Python Measurement Package using venv

1. Make sure the system has the recommended python version installed.

2. Open a command prompt, change the working directory to the directory of your choice where you want to create a project.

    ``` cmd
    cd <path_of_directory_of_your_choice>
    ```

3. Create a virtual environment.

    ``` cmd
    REM This creates a virtual environment named .venv
    python -m venv .venv
    ```

4. Activate the virtual environment.After successful activation

    ``` cmd
    .venv\scripts\activate
    REM Optionally upgrade the pip within the venv by executing the command
    python -m pip install -U pip
    ```

5. Install the `ni_measurement_service-x.x.x`.tar.gz package into the virtual environment.

    ``` cmd
    pip install <path_of_ni_measurement_service-x.x.x.tar.gz>
    ```

6. Create measurement modules as described in ["Developing a minimal python measurement"](#developing-a-minimal-python-measurement)
    - Any additional dependencies required by measurement can be added pip install.

        ``` cmd
        pip install <dependency_package_name>
        ```

For detailed info on managing projects with a virtual environment [refer to the official documentation](https://docs.python.org/3/tutorial/venv.html).

### Create and Manage Python Measurement Package by directly installing NIMS as a system-level package

Measurement developers can also install the NIMS framework as a system package if their requirement is demanding.

1. Install the `ni_measurement_service-x.x.x`.tar.gz package from the command prompt

    ``` cmd
    pip install <path_of_ni_measurement_service-x.x.x.tar.gz>
    ```

2. Create measurement modules as described in ["Developing a minimal python measurement"]

---

## Examples

The list of python measurement example projects.

1. **Sample measurement**: Sample Measurement is a simple python-based example that has configurations defined for all supported data types. The measurement logic simply assigns the configuration values to respective output values.
2. **DC Measurements**: Simple python measurement example that interacts with DCPower 4145 Instrument.
    1. DC Measurement with Screen file UI
    2. DC Measurement with LabVIEW UI

### Setting up the Example Measurements

The example measurements shared are based on poetry. Follow the below steps to  for setting up the example measurement:

1. Install `poetry` if not already installed. Refer to <https://python-poetry.org/docs/#installation> for information on installing poetry.

2. Open a command prompt, change the working directory to the directory of the example measurement you want to work with.

    ``` cmd
    cd <path_of_example_measurement>
    REM Example: cd "..\examples\dc_measurement"
    ```

3. Install the dependency needed for the Example into `.venv`

    ``` cmd
    poetry install
    ```

### Executing the Example Measurements

1. [Run the measurement](#steps-to-run-a-measurement-service) by executing the `measurement.py` python file.

2. To Exit the measurement service, press `Enter` in the terminal to properly close the service.

---
