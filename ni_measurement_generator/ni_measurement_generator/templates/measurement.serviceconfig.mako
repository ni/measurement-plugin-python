<%page args="display_name, service_class, description_url"/>\
\
{
  "services": [
    {
      "displayName": "${display_name}",
      "serviceClass": "${service_class}",
      "descriptionUrl": "${description_url}",
      "providedInterfaces": [ "ni.measurementlink.measurement.v1.MeasurementService" ],
      "path": "start.bat"
    }
  ]
}