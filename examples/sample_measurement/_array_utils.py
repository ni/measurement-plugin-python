"""Double2DArray Conversion Utilities."""

from __future__ import annotations

from typing import TYPE_CHECKING, List

from ni_measurement_plugin_sdk_service._internal.stubs.ni.protobuf.types import (
    array_pb2,
)

if TYPE_CHECKING:
    import numpy as np
    import numpy.typing as npt


def double2darray_to_ndarray(double2darray: array_pb2.Double2DArray) -> npt.NDArray[np.float64]:
    """Convert Double2DArray to numpy NDArray."""
    import numpy as np

    return np.array(double2darray.data, dtype=np.float64).reshape(
        double2darray.rows, double2darray.columns
    )


def ndarray_to_double2darray(ndarray: npt.NDArray[np.float64]) -> array_pb2.Double2DArray:
    """Convert numpy NDArray to Double2DArray."""
    return array_pb2.Double2DArray(
        data=ndarray.flatten().tolist(), rows=ndarray.shape[0], columns=ndarray.shape[1]
    )


def list_to_double2darray(data: List[List[float]]) -> array_pb2.Double2DArray:
    """Convert list of lists to Double2DArray."""
    rows = len(data)
    columns = len(data[0]) if rows > 0 else 0
    flattened_data = [item for sublist in data for item in sublist]
    return array_pb2.Double2DArray(data=flattened_data, rows=rows, columns=columns)


def double2darray_to_list(double2darray: array_pb2.Double2DArray) -> List[List[float]]:
    """Convert Double2DArray to list of lists."""
    data = double2darray.data
    rows = double2darray.rows
    columns = double2darray.columns
    return [data[i * columns : (i + 1) * columns] for i in range(rows)]
