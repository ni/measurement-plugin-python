# Proto files

## `session.proto`

`session.proto` originally came from NI grpc-device. Its contents and relative file path
must match nimi-python, or else the `protobuf` will raise "duplicate symbol" errors. It
is checked into this Git repo in order to reuse the `Session` message in the MeasurementLink
`.proto` files.

Origin:
- Git repo: https://github.com/ni/nimi-python/blob/master/src/shared_protos/session.proto
- Commit hash: c9787038978642a257b85c452f097469369ad184

## `ni/measurementlink`

These are the MeasurementLink `.proto` files. They should be identical to the version in
NI's internal ASW repo, except `nidevice_grpc/session.proto` imports have been updated
to use `session.proto` instead.