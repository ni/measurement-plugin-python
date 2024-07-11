from examples.DAQ.NI_DAQmx_Analog_Input.ni_daq_analog_input import measure, cancel, register_pin_map, async_measure
import asyncio
import concurrent.futures

async def another_method():
    print("Entered into 2nd method")
    await asyncio.sleep(10)
    print("after 10 secs wait")
    cancel()
    print("Executed another method after 10 seconds")

async def call_async_measure(loop):
    with concurrent.futures.ThreadPoolExecutor() as pool:
        response = await loop.run_in_executor(pool, async_measure)
    print(f"gRPC response: {response}")

async def main():
    # Get the current event loop
    loop = asyncio.get_running_loop()
    # Schedule the gRPC method and the other method
    grpc_task = asyncio.create_task(call_async_measure(loop))
    another_task = asyncio.create_task(another_method())
    # Wait for both tasks to complete
    await asyncio.gather(grpc_task, another_task)

# Run the main function
asyncio.run(main())