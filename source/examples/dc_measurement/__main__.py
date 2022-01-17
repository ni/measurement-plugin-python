"""
Startup File
"""
import core.measurement_service as measurement_service

"""
Driver Method
"""
if __name__ == "__main__":
    port = measurement_service.serve()
