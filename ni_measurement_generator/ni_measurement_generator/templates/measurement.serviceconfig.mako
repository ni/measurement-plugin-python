<%page args="display_name, service_class, description"/>\
\
{
  "services": [
    {
      "displayName": "${display_name}",
      "serviceClass": "${service_class}",
      "descriptionUrl": "${description}",
      "providedInterfaces": [ "ni.measurements.v1.MeasurementService" ],
      "path": "start.bat"
    }
  ]
}