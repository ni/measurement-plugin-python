# Measurement Services Support for Python

This repo contains the necessary Python Measurement templates and examples to call into the Measurement Services.

Recommended Python Version: 3.8

## Getting started with Python measurements

## Steps to setup a measurement

**Setting up measurement project using poetry** 

1. Make sure the system has the recommended python version installed.

2. Install `poetry` using the installation steps given in https://python-poetry.org/docs/#installation.

3. Open command prompt in the folder where the python project is to be created and run the command `poetry new <name of the project>`.

4. Add the `ni_measurement_service-x.x.x` package by running the command `poetry add <path_of_ni_measurement_service-x.x.x.tar.gz>`.
    - A virtual environment will be setup.
    - The dependencies given will be installed into the virtual environment.

5. Add futher required project dependencies using `poetry add <dependency name>`.

**Setting up measurement project by manually creating the virtual environment.** 

1. Make sure the system has the recommended python version installed.

2. Create a new directory for containing the measurement files.

3. Open a command prompt and change the working directory to the newly created directory.

3. Create a virtual environment.
    - Command: `python -m venv .venv`. This creates a virtual environment named venv

4. Activate the virtual environment.
    - Command : `.venv\scripts\activate`.
    - After successful activation, you can see the name of the environment, `(.venv)` is added to the command prompt.
    - Optionally upgrade the pip within the venv by executing the command: `python -m pip install -U pip`

5. Install the `ni_measurement_service-x.x.x`.tar.gz file into the virtual environment.
    - Install the file using `pip install <path_of_ni_measurement_service-x.x.x.tar.gz>`

**Setting up measurement project without virtual environment**

1. Make sure the system has the recommended python version installed.

2. Install the `ni_measurement_service-x.x.x`.tar.gz file into the virtual environment.
    - Install the file using `pip install <path_of_ni_measurement_service-x.x.x.tar.gz>` 

Note: This will add the `ni_measurement_service-x.x.x` as a system-wide python package.


## Steps to create a new measurement service.

1. Create a new python file.

2. Import the items shown in the snippet. These imports get the required definitions for setting up a measurement.
``` python
from ni_measurement_service.measurement.info import DataType
from ni_measurement_service.measurement.info import MeasurementInfo
from ni_measurement_service.measurement.info import ServiceInfo
from ni_measurement_service.measurement.info import UIFileType
from ni_measurement_service.measurement.service import MeasurementService
```

3. Define `measurement_info` and `service_info` with the required details, as shown in the snippet below:
``` python
measurement_info = MeasurementInfo(
    display_name="FooMeasurement",
    version="0.1.0.0",
    measurement_type="",
    product_type="",
    ui_file_path="",
    ui_file_type="",
)

service_info = ServiceInfo(
    service_class="FooMeasurement_Python",
    service_id="<GUID>",
    description_url="",
)
```
4. Create a new `MeasurementService` Instance.
``` python
foo_measurement_service = MeasurementService(measurement_info, service_info)
```

5. Define a function to perform the measurement. The measurement function can have any name.
    - To register the measurement function use the `register_measurment` decorartor from the `MeasurmentService` instance.
    ``` python
    @foo_measurement_service.register_measurement
    def measure(input_1, input_2):
    ```

6. Define the configuration parameters required by the measurement 
    - Use the `configuration()` decorator to defne the configuartions
    ``` python 
    @foo_measurement_service.register_measurement
    @foo_measurement_service.configuration("Input 1", DataType.String, "default value")
    @foo_measurement_service.configuration("Input 2", DataType.String, "default value")
    def measure(input_1, input_2):
    ```
    - One thing to note is that the order of the decorators from top to bottom must match the
    order of the parameters in the `measure` function. For example, in the snippet above the
    decorator for "Input 1" will be mapped to the `input_1` parameter and "Input 2" will be mapped to `input_2` parameter.
7. Define the ouput parameters required by the measurement.
    - Use the `output()` decorator available in the `MeasurementService` instance
    ``` python
    @foo_measurement_service.register_measurement
    @foo_measurement_service.configuration("Input 1", DataType.String, "default value")
    @foo_measurement_service.configuration("Input 2", DataType.String, "default value")
    @foo_measurement_service.output("Output 1", DataType.String)
    @foo_measurement_service.output("Output 2", DataType.String)
    def measure(input_1, input_2):
        return ["foo", "bar"]
    ```
    - The measurement function must return the outputs as a list.
    - One thing to note is that the order of the decorators from top to bottom must match the
    order of the values of the list returned by the `measure` function. For example, in the snippet above, the output named "Output 1" will have the value "foo" and the output named "Output 2" will have the value "bar"

8. Add the startup logic that is to be executed when the measurement is started.
    - To start the service call the `host_as_grpc_service()` from the `MeasurementService` instance.
    - Use the close_service() function to terminate the service.
    - A typical implementation is shown below
    ``` python
    if __name__ == "__main__":
        foo_measurement_service.host_as_grpc_service()
        input("To Exit during the Service lifetime, Press Enter.\n")
        foo_measurement_service.close_service()
    ```

## Steps to run a measurement service.

1. Start the discovery service if not already started. 

2. Activate the virtual environment if not already activated.
    - Command : `.venv\scripts\activate`.
    - After successful activation, you can see the name of the environment, `(.venv)` is added to the command prompt.

3. Run the measurement file to start the measurement as a service, after which the measurement can be used in clients like Teststand or InstrumentStudio.

4. After the usage of measurement, deactivate the virtual environment.
     - Command : `deactivate`.

## Examples

1. ### DC Measurement
    DC Measurement is a simple python based example that interacts with DCPower 4145 Instrument.

    #### Steps to run the dc_measurement

    1. **Setting up python with required dependency.** This step is only for first-time users.
        1.  The measurement file can be found in  `..\examples\dc_measurement` 
        
        2. Install `poetry` if not already installed. Refer to https://python-poetry.org/docs/#installation for information on installing poetry.
        
        3. Open command prompt in the directory and run the command `"poetry install"`
            - A virtual environment will be setup.
            - All the dependencies required by the project will be installed.

    2. [Run the measurment](#steps-to-run-a-measurement-service) using the `measurement.py` python file. hit Enter in the python terminal to close the service.


    #### Overview on the Components of dc_measurement
    1. measurement.py
        - This file contains all the details related to the measurement and also contains the logic for the measurement execution.
        - This file is run to start the measurment as a service.

    2. DCMeasurementScreen.isscr
        - UI file for the Measurement.
        - The path and type of this file is configured by `ui_file_path` and `ui_file_type` respectively in `measurement_info` variable definition in `measurement.py`.

2. ### DC Measurement with LabVIEW UI
    This example is similar to the [dc_measurement example](#steps-to-run-the-dcmeasurement)  example, with the only difference being the UI used. This example uses a LabVIEW VI as the UI element.

3. ### Sample Measurement
    Sample Measurement is a simple python-based example that has configurations defined for all supported datatypes. The measurement logic simply assigns the configuration values to respective output values.

    #### Steps to run the sample_measurement
    - The measurment files can be found in `..\examples\sample_measurement` .
    - Follow the same steps provided in the [dc_measurement example](#steps-to-run-the-dcmeasurement) documentation with the sample_measurement files to use the sample_measurement example.

    #### Overview on the Components of sample_measurement
    - Similar to the [dc_measurement example](#overview-on-the-components-of-dcmeasurement) the sample_measurement example also contains a `measurement.py` to start the measurement service and  a UI file named `SamplemeasurmentScreen.isscr` for the UI.
