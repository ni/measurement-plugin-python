<%page args="display_name, service_class, service_id, description, ui_file_type"/>\
\
{
  "services": [
    {
      "id": "${service_id}", 
      "name": "${display_name}", 
      "serviceClass": "${service_class}", 
      "descriptionUrl": "${description}",
      "providedServices": [ "ni.measurements.v1.MeasurementService" ], 
      "attributes": [ "UserInterfaceType=${ui_file_type}" ],
      "path": "start.bat" 
    }
  ]
}