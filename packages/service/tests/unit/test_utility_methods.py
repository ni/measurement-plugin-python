import numpy
import numpy.typing

from ni_measurement_plugin_sdk_service._internal.stubs.ni.protobuf.types import (
    array_pb2,
)
from tests.utilities import _array_utils


def test___double2darray_to_ndarray():
    double2darray = array_pb2.Double2DArray(data=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0], rows=2, columns=3)
    ndarray = _array_utils.double2darray_to_ndarray(double2darray)
    assert numpy.array_equal(ndarray, numpy.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]))


def test___ndarray_to_double2darray():
    ndarray = numpy.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])
    double2darray = _array_utils.ndarray_to_double2darray(ndarray)
    assert double2darray == array_pb2.Double2DArray(
        data=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0], rows=2, columns=3
    )


def test___list_to_double2darray():
    data = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
    double2darray = _array_utils.list_to_double2darray(data)
    assert double2darray == array_pb2.Double2DArray(
        data=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0], rows=2, columns=3
    )


def test___double2darray_to_list():
    double2darray = array_pb2.Double2DArray(data=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0], rows=2, columns=3)
    data = _array_utils.double2darray_to_list(double2darray)
    assert data == [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
