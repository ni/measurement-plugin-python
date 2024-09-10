from sample_measurement_client import SampleMeasurementClient, EInEnum



def main():
    my_obj = SampleMeasurementClient()
    result = my_obj.measure(e___in=EInEnum.RED)
    print(result)

if __name__ == "__main__":
    main()