"""A default measurement with an array in and out."""
import logging
import pathlib
import random
import time

import click
import ni_measurementlink_service as nims
from ni_measurementlink_service._internal.stubs.ni.protobuf.types import xydata_pb2

service_directory = pathlib.Path(__file__).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "game_of_life.serviceconfig",
    version="1.0.0.0",
    ui_file_paths=[service_directory / "game_of_life.measui"],
)


@measurement_service.register_measurement
@measurement_service.configuration("width", nims.DataType.UInt32, 100)
@measurement_service.configuration("height", nims.DataType.UInt32, 100)
@measurement_service.configuration("update_interval", nims.DataType.UInt32, 100)
@measurement_service.output("game_of_life", nims.DataType.DoubleXYData)
@measurement_service.output("generation", nims.DataType.UInt32)
def measure(width, height, update_interval):
    """Streaming measurement that returns Conway's Game of Life grid as DoubleXYData."""
    grid = initialize_grid_with_seeded_data(width, height)
    generation = 0
    while True:
        generation += 1;

        xydata = initialize_xydata_and_frame(width, height)
        rowIndex = 0
        for row in grid:
            colIndex = 0
            for cell in row:
                if cell:
                    xydata.x_data.append(rowIndex)
                    xydata.y_data.append(colIndex)
                colIndex += 1
            rowIndex += 1
        grid = update_grid(grid)
        xydata_out = xydata
        generation += 1
        time.sleep(update_interval / 1000)

        yield (xydata_out, generation)


def initialize_xydata_and_frame(width, height) -> xydata_pb2.DoubleXYData:
    xydata = xydata_pb2.DoubleXYData()

    # Frame To keep the graph stable
    xydata.x_data.append(-1)
    xydata.y_data.append(-1)
    xydata.x_data.append(-1)
    xydata.y_data.append(height + 1)
    xydata.x_data.append(width + 1)
    xydata.y_data.append(-1)
    xydata.x_data.append(width + 1)
    xydata.y_data.append(height + 1)
    return xydata

def initialize_grid_with_seeded_data(rows, cols, probability=0.6):
    return [[random.random() < probability for _ in range(cols)] for _ in range(rows)]

def initialize_grid(rows, cols):
    return [[False for _ in range(cols)] for _ in range(rows)]

def count_neighbors(grid, row, col):
    count = 0
    neighbors = [
        (row - 1, col - 1),
        (row - 1, col),
        (row - 1, col + 1),
        (row, col - 1),
        (row, col + 1),
        (row + 1, col - 1),
        (row + 1, col),
        (row + 1, col + 1),
    ]
    for r, c in neighbors:
        if 0 <= r < len(grid) and 0 <= c < len(grid[0]) and grid[r][c]:
            count += 1
    return count


def update_grid(grid):
    new_grid = initialize_grid(len(grid), len(grid[0]))
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            neighbors = count_neighbors(grid, row, col)
            if grid[row][col]:
                new_grid[row][col] = neighbors == 2 or neighbors == 3
            else:
                new_grid[row][col] = neighbors == 3
    return new_grid


@click.command
@click.option(
    "-v",
    "--verbose",
    count=True,
    help="Enable verbose logging. Repeat to increase verbosity.",
)
def main(verbose: int) -> None:
    """Host the game_of_life service."""
    if verbose > 1:
        level = logging.DEBUG
    elif verbose == 1:
        level = logging.INFO
    else:
        level = logging.WARNING
    logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s", level=level)

    with measurement_service.host_service():
        input("Press enter to close the measurement service.\n")


if __name__ == "__main__":
    main()
