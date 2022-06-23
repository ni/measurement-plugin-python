poetry run python -m grpc_tools.protoc -I proto --python_out=. --grpc_python_out=. ServiceLocation.proto DiscoveryServices.proto Measurement.proto ServiceManagement.proto && ^
poetry run black *.py