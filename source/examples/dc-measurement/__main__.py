"""
Startup File
"""
import core.MeasurementService as MeasurementService
import core.test as test

"""
Driver Method
"""
if __name__ == "__main__":
    # test.run()
    port = MeasurementService.serve()
