<%page args="import_name, class_defs"/>\
\

import collections.abc
import typing

import grpc
import stubs.${import_name}_pb2 as ${import_name}_pb2
% for class_name, method_defs in class_defs.items():
from stubs.${import_name}_pb2_grpc import ${class_name}


class ${class_name[:-1]}(${class_name}):

    def __init__(self):
        pass

    % for method_def in method_defs:
    def ${method_def.name}(
        ${method_def.request_type}
    ) -> ${method_def.return_type}:
        raise NotImplementedError("Method is not implemented!")

    % endfor
% endfor
