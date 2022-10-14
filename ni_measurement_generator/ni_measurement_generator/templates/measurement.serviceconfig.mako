<%page args="display_name, service_class, service_id, description"/>\
\
{
  "services": [
    {
      "id": "${service_id}", 
      "name": "${display_name}", 
      "serviceClass": "${service_class}", 
      "descriptionUrl": "${description}",
      "providedServices": [ "ni.measurements.v1.MeasurementService" ], 
      "path": "start.bat" 
    }
  ]
}