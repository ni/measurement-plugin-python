"""2DArray Conversion Utilities."""

from __future__ import annotations

from typing import TYPE_CHECKING

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


def list_to_double2darray(data: list[list[float]]) -> array_pb2.Double2DArray:
    """Convert list of lists to Double2DArray."""
    rows = len(data)
    columns = len(data[0]) if rows > 0 else 0
    flattened_data = [item for sublist in data for item in sublist]
    return array_pb2.Double2DArray(data=flattened_data, rows=rows, columns=columns)


def double2darray_to_list(double2darray: array_pb2.Double2DArray) -> list[list[float]]:
    """Convert Double2DArray to list of lists."""
    data = double2darray.data
    rows = double2darray.rows
    columns = double2darray.columns
    return [data[i * columns : (i + 1) * columns] for i in range(rows)]


def string2darray_to_ndarray(string2darray: array_pb2.String2DArray) -> npt.NDArray[np.str_]:
    """Convert String2DArray to numpy NDArray."""
    import numpy as np

    return np.array(string2darray.data, dtype=np.str_).reshape(
        string2darray.rows, string2darray.columns
    )


def ndarray_to_string2darray(ndarray: npt.NDArray[np.str_]) -> array_pb2.String2DArray:
    """Convert numpy NDArray to String2DArray."""
    return array_pb2.String2DArray(
        data=ndarray.flatten().tolist(), rows=ndarray.shape[0], columns=ndarray.shape[1]
    )


def string2darray_to_list(string2darray: array_pb2.String2DArray) -> list[list[str]]:
    """Convert String2DArray to list of lists."""
    data = string2darray.data
    rows = string2darray.rows
    columns = string2darray.columns
    return [data[i * columns : (i + 1) * columns] for i in range(rows)]


def list_to_string2darray(data: list[list[str]]) -> array_pb2.String2DArray:
    """Convert list of lists to String2DArray."""
    rows = len(data)
    columns = len(data[0]) if rows > 0 else 0
    flattened_data = [item for sublist in data for item in sublist]
    return array_pb2.String2DArray(data=flattened_data, rows=rows, columns=columns)
