<%page args="display_name, service_class, description_url, description, collection, tags"/>\
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
              "annotations": {
                  "ni/service.description": description,
                  "ni/service.collection": collection,
                  "ni/service.tags": tags
              },
          }
       ]
    }
%>\
${json.dumps(service_config, indent=2)}