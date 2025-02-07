import numpy
import numpy.typing

from ni_measurement_plugin_sdk_service._internal.stubs.ni.protobuf.types import (
    array_pb2,
)
from tests.utilities import _array_utils


def test___valid_double2darray___double2darray_to_ndarray___converts_data():
    double2darray = array_pb2.Double2DArray(data=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0], rows=2, columns=3)

    ndarray = _array_utils.double2darray_to_ndarray(double2darray)

    assert numpy.array_equal(ndarray, numpy.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]))


def test___valid_ndarray___ndarray_to_double2darray___converts_data():
    ndarray = numpy.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]])

    double2darray = _array_utils.ndarray_to_double2darray(ndarray)

    assert double2darray == array_pb2.Double2DArray(
        data=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0], rows=2, columns=3
    )


def test___valid_list___list_to_double2darray___converts_data():
    data = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]

    double2darray = _array_utils.list_to_double2darray(data)

    assert double2darray == array_pb2.Double2DArray(
        data=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0], rows=2, columns=3
    )


def test___valid_double2darray___double2darray_to_list___converts_data():
    double2darray = array_pb2.Double2DArray(data=[1.0, 2.0, 3.0, 4.0, 5.0, 6.0], rows=2, columns=3)

    data = _array_utils.double2darray_to_list(double2darray)

    assert data == [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]


def test___valid_string2darray___string2darray_to_ndarray___converts_data():
    string2darray = array_pb2.String2DArray(data=["a", "b", "c", "d", "e", "f"], rows=2, columns=3)

    ndarray = _array_utils.string2darray_to_ndarray(string2darray)

    assert numpy.array_equal(ndarray, numpy.array([["a", "b", "c"], ["d", "e", "f"]]))


def test___valid_ndarray___ndarray_to_string2darray___converts_data():
    ndarray = numpy.array([["a", "b", "c"], ["d", "e", "f"]])

    string2darray = _array_utils.ndarray_to_string2darray(ndarray)

    assert string2darray == array_pb2.String2DArray(
        data=["a", "b", "c", "d", "e", "f"], rows=2, columns=3
    )


def test___valid_list___list_to_string2darray___converts_data():
    data = [["a", "b", "c"], ["d", "e", "f"]]

    string2darray = _array_utils.list_to_string2darray(data)

    assert string2darray == array_pb2.String2DArray(
        data=["a", "b", "c", "d", "e", "f"], rows=2, columns=3
    )


def test___valid_string2darray___string2darray_to_list___converts_data():
    string2darray = array_pb2.String2DArray(data=["a", "b", "c", "d", "e", "f"], rows=2, columns=3)

    data = _array_utils.string2darray_to_list(string2darray)

    assert data == [["a", "b", "c"], ["d", "e", "f"]]
