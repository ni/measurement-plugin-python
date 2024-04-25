# Python Measurement Client

## Expected Workflow

1. Get the list of measurement services.
2. Resolve the measurement which is selected for execution.
3. Validate and construct a configuration and output metadata dictionary with the measurement's input-output
   parameters.
4. Deserialize the default values.
5. In case of pin-centric measurement, register the pin map file with the pin map service
6. Serialize the measurement configuration values.
7. Invoke the measurement.
8. Deserialize the measurement output values.

## Things needed to Create a Measurement Client

1. Discovery Client
2. Pin Map Client
3. Measurement Client Stub
4. Serialization and Deserialization

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

### 4. Serialization and Deserialization

- The following must be ensured to use the existing serialization and deserialization
  implementation.
  - Serialization
    - A dictionary should be constructed for the configuration metadata with key as *field number*
     and the value being the *parameter's metadata*.
    - The values of the configuration parameters in the order of their field number.
  - Deserialization
    - A dictionary should be constructed for the output metadata with key as *field number* and the
      value being the *parameter's metadata*.  

  *Note*: The existing `ParameterMetadata` container expects a default value which is used for enum
  parameters. This requires us to pass in a default value for the enum parameter which could just be
  0 for simplicity.

## Things to be added

- Exposing `enumerate_services` API in the discovery client and support class (Service Descriptor).
- Creating a pin map client.
- A measurement client wrapping the corresponding RPC APIs with required helper APIs say for
  validating the metadata, abstracting the v1 and v2 versions, data parsing etc.
- Preferably generalizing or specializing the serialization and deserialization APIs.
- Possibly explore ways to edit the configuration parameter values.
