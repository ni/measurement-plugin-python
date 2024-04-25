# Python Script to Run Measurements

## Problem Statement

- Currently, the users can run LabVIEW and Python measurements from InstrumentStudio and TestStand.
- If they want to run measurements say using LabVIEW or Python, the current workflow requires
  expertise on Python and gRPC technologies along with a very good understanding of
  MeasurementLink.

## Implementation

1. Using the discovery client, get the list of active measurement services.
2. Using the measurement client, for a selected measurement, get the measurement's parameter metadata.
3. If the measurement is pin-centric, get and register the pin map file with the pin map service by
  using the pin map client
4. Run the measurement.

## Things needed to Create a Measurement Client

1. Discovery Client
2. Pin Map Client
3. Measurement Client Stub
4. Parameter Serialization and Deserialization

### 1. Discovery Client

- Interacts with discovery service to get the list of active measurement services and to
  resolve their location.
- RPC APIs involved: `EnumerateServices`, `ResolveService`.

### 2. Pin Map Client

- Communicates with pin map service to register and update the pin map file.
  - We can also use this to retrieve the pins given instrument type or the resource information
    given the pins.
- RPC APIs involved: `UpdatePinMapFromXmlRequest`.

### 3. Measurement Client Stub

- Interacts with the measurement service to get its metadata and to make the measure call.
- RPC APIs involved: `GetMetadata`, `Measure`.

### 4. Parameter Serialization and Deserialization

- Since the datatype of a measurement's configuration and output parameters are dynamic, its values
  are parsed manually by serializing and deserializing it during `GetMetadata` and `Measure` calls.
- The following must be ensured to use the existing serialization and deserialization
  implementation.
  - Serialization
    - A dictionary should be constructed for the configuration metadata with key as *field number*
     and the value being the *parameter's metadata*.
    - The values of the configuration parameters should be in the order of their field number.
  - Deserialization
    - A dictionary should be constructed for the output metadata with key as *field number* and the
      value being the *parameter's metadata*.  

  *Note*: The existing `ParameterMetadata` container expects a default value which is used for enum
  parameters. This requires us to pass in a default value for the enum parameter which could just be
  0 for simplicity.

## Yet to be added

- Exposing `enumerate_services` API in the discovery client and support class (Service Descriptor).
- Creating a fully fledged pin map client.
- A measurement client library wrapping the RPC APIs with required helper APIs say for validating
  the metadata, abstracting the v1 and v2 versions, parsing data, etc.
  - Preferably generalize or specialize the serialization and deserialization API implementation.
  - Possibly explore ways to easily facilitate editing the configuration parameter values for any
    datatype in a selected measurement.
