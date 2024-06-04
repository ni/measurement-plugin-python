<%page args="import_name, gen_file_name, class_name, method_name"/>\
\

import grpc
from grpc.framework.foundation import logging_pool

from ${gen_file_name} import ${class_name}
import ${import_name}_pb2_grpc
from ni_measurementlink_service.discovery import DiscoveryClient, ServiceLocation
from ni_measurementlink_service.measurement.info import ServiceInfo

_SERVICE_CLASS = "UPDATE THIS STRING"

if __name__ == "__main__":
    servicer = ${class_name}()
    server = grpc.server(
            logging_pool.pool(max_workers=10),
            options=[
                ("grpc.max_receive_message_length", -1),
                ("grpc.max_send_message_length", -1),
            ],
        )
    ${import_name}_pb2_grpc.${method_name}(servicer, server)

    host = "[::1]"
    port = str(server.add_insecure_port(f"{host}:0"))
    address = f"http://{host}:{port}"
    server.start()
    print(f"[INFO] The server is now listening on 'localhost:{port}'")

    discovery_client = DiscoveryClient()
    service_location = ServiceLocation("localhost", port, "")
    service_info = ServiceInfo(_SERVICE_CLASS, "", ["ni.measurementlink.drivers"], display_name="NI-VISA DMM")
    registration_id = discovery_client.register_service(service_info=service_info, service_location=service_location)

    _ = input("Press enter to stop the server.")
    discovery_client.unregister_service(registration_id)
    server.stop(grace=5)
