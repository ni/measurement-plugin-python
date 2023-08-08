"""Contains indicators to identify the Production/Test environment.
"""


class GlobalTestingState:
    """Indicator for measurement running in testing environment."""

    IsInTestState: bool = False
