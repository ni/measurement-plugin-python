import asyncio
import concurrent.futures
from examples.test.testMeasurement.abc.abc import measure, register_pin_map, cancel

async def task1(loop):
    register_pin_map(r"D:\Meas-Link\repos\measurementlink-python\examples\nidaqmx_analog_input\NIDAQmxAnalogInput.pinmap")
    
    with concurrent.futures.ThreadPoolExecutor() as pool:
        response = await loop.run_in_executor(pool, measure, "Pin1", 1000, 60000)
    
    print(response)

async def task2():
    for i in range(5):
        print(f"Task 2 - Iteration {i}")
        await asyncio.sleep(1)  # Simulate an I/O operation
    cancel()

async def main():
    loop = asyncio.get_running_loop()
    task1_coroutine = task1(loop)
    task2_coroutine = task2()
    
    await asyncio.gather(task1_coroutine, task2_coroutine)

# Run the main function
asyncio.run(main())
