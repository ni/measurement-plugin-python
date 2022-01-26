#!/usr/bin/env python3

"""
Startup File
"""

import sys
from pathlib import Path

"""
Driver Method
"""
if __name__ == "__main__":
    # core_path can be removed when the measurement_services_core is installed a python package.
    core_path = str(Path(__file__).resolve().parents[2]) + "\\source\\measurement_services_core"
    sys.path.append(core_path)
    measurement_service = __import__("measurement_service")
    measurement_service.serve()
    input("To Exit during the Service lifetime, Press Enter.\n")
    measurement_service.unregister_stop_service()
