"""Source the XY data for Conway's Game of Life."""
import pathlib
import random
import time
from typing import Any, Generator, List, Tuple

import click
from _helpers import configure_logging, verbosity_option

import ni_measurementlink_service as nims
from ni_measurementlink_service._internal.stubs.ni.protobuf.types import xydata_pb2

service_directory = pathlib.Path(__file__).resolve().parent
measurement_service = nims.MeasurementService(
    service_config_path=service_directory / "game_of_life.serviceconfig",
    version="1.0.0.0",
    ui_file_paths=[service_directory / "game_of_life.measui"],
)

Grid = List[List[bool]]


@measurement_service.register_measurement
@measurement_service.configuration("width", nims.DataType.UInt32, 100)
@measurement_service.configuration("height", nims.DataType.UInt32, 100)
@measurement_service.configuration("update_interval", nims.DataType.UInt32, 100)
@measurement_service.output("game_of_life", nims.DataType.DoubleXYData)
@measurement_service.output("generation", nims.DataType.UInt32)
def measure(
    width: int, height: int, update_interval: int
) -> Generator[Tuple[xydata_pb2.DoubleXYData, int], None, None]:
    """Streaming measurement that returns Conway's Game of Life grid as DoubleXYData."""
    grid = _initialize_grid_with_seeded_data(width, height)
    generation = 0
    while True:
        generation += 1

        xydata = _initialize_xydata_and_frame(width, height)
        row_index = 0
        for row in grid:
            col_index = 0
            for cell in row:
                if cell:
                    xydata.x_data.append(row_index)
                    xydata.y_data.append(col_index)
                col_index += 1
            row_index += 1
        grid = _update_grid(grid)
        xydata_out = xydata
        generation += 1
        time.sleep(update_interval / 1000)

        yield (xydata_out, generation)


def _initialize_xydata_and_frame(width: int, height: int) -> xydata_pb2.DoubleXYData:
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


def _initialize_grid_with_seeded_data(rows: int, cols: int, probability: float = 0.6) -> Grid:
    return [[random.random() < probability for _ in range(cols)] for _ in range(rows)]


def _initialize_grid(rows: int, cols: int) -> Grid:
    return [[False for _ in range(cols)] for _ in range(rows)]


def _count_neighbors(grid: Grid, row: int, col: int) -> int:
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


def _update_grid(grid: Grid) -> Grid:
    new_grid = _initialize_grid(len(grid), len(grid[0]))
    for row in range(len(grid)):
        for col in range(len(grid[0])):
            neighbors = _count_neighbors(grid, row, col)
            if grid[row][col]:
                new_grid[row][col] = neighbors == 2 or neighbors == 3
            else:
                new_grid[row][col] = neighbors == 3
    return new_grid


@click.command
@verbosity_option
def main(verbosity: int, **kwargs: Any) -> None:
    """Source the XY data for Conway's Game of Life."""
    configure_logging(verbosity)

    with measurement_service.host_service():
        input("Press enter to close the measurement service.\n")


if __name__ == "__main__":
    main()
