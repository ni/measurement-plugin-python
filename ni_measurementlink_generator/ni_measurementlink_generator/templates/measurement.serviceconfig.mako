<%page args="display_name, service_class, description_url, description, collection, tags"/>\
\
{
  "services": [
    {
      "displayName": "${display_name}",
      "serviceClass": "${service_class}",
      "descriptionUrl": "${description_url}",
      "providedInterfaces": [ "ni.measurementlink.measurement.v1.MeasurementService" ],
      "path": "start.bat",
      "annotations": {
        "ni/service.description": "${description}",
        "ni/service.collection": "${collection}",
        "ni/service.tags": ${tags}
      }
    }
  ]
}