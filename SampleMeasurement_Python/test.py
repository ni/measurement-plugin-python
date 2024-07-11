from SampleMeasurement_Python.SampleMeasurement_Python_client import measure


response = measure()

for res in response:
    print(res)