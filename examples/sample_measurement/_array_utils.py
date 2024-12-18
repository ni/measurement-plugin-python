"""Double2DArray Conversion Utilities."""

from typing import Any

from ni_measurement_plugin_sdk_service._internal.stubs.ni.protobuf.types import (
    array_pb2,
)

try:
    import numpy as np
    from numpy.typing import NDArray

    def double2darray_to_ndarray(double2darray: array_pb2.Double2DArray) -> NDArray[np.float64]:
        """Convert Double2DArray to numpy NDArray."""
        return np.array(double2darray.data, dtype=np.float64).reshape(
            double2darray.rows, double2darray.columns
        )

    def ndarray_to_double2darray(ndarray: NDArray[np.float64]) -> array_pb2.Double2DArray:
        """Convert numpy NDArray to Double2DArray."""
        return array_pb2.Double2DArray(
            data=ndarray.flatten().tolist(), rows=ndarray.shape[0], columns=ndarray.shape[1]
        )

except ImportError:
    np = None

    def double2darray_to_ndarray(double2darray: array_pb2.Double2DArray) -> Any:
        """Raise ImportError if numpy is not available."""
        raise ImportError("NumPy is not available. Install NumPy to use this function.")

    def ndarray_to_double2darray(ndarray: Any) -> array_pb2.Double2DArray:
        """Raise ImportError if numpy is not available."""
        raise ImportError("NumPy is not available. Install NumPy to use this function.")


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
