<%page args="display_name, service_class, description_url"/>\
<%
    import json

    service_config = {
        "services": [
            {
                "displayName": display_name,
                "serviceClass": service_class,
                "descriptionUrl": description_url,
                "providedInterfaces": [
                    "ni.measurementlink.measurement.v1.MeasurementService",
                    "ni.measurementlink.measurement.v2.MeasurementService",                   
                ],
                "path": "start.bat",
            }
        ]
    }
%>\
${json.dumps(service_config, indent=2)}