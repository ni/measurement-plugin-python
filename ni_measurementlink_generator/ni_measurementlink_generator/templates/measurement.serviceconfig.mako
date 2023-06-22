<%page args="display_name, service_class, description_url, annotations_description, collection, tags"/>\
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
        "ni/service.description": "${annotations_description}",
        "ni/service.collection": "${collection}",
        "ni/service.tags": ${tags}
      }
    }
  ]
}