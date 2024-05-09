<%page args="module_name, description"/>\
\
[tool.poetry]
name = "${module_name}"
version = "0.1.0"
description = "${description}"
authors = ["National Instruments"]

[tool.poetry.dependencies]
python = "^3.8"
grpcio = "^1.49.1"
protobuf = "^4.21"
ni-measurementlink-service = { git = "https://github.com/ni/measurementlink-python.git", branch = "users/jay/python-measurement-client"}

[tool.poetry.group.dev.dependencies]
ni-python-styleguide = ">=0.4.1"
mypy = ">=1.0"

[tool.black]
line-length = 100

[tool.mypy]
disallow_untyped_defs = true
