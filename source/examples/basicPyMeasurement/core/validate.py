from ast import Index
import functools
import inspect


class Validated(type):

    """
    Base meta-class for our validation classes.
    """

    def __getitem__(self, type):
        """
        Implements the type specialization via subscription.
        """
        return lambda *args, **kwargs: self(*args, **kwargs, type=type)


class TypeChecked(metaclass=Validated):
    def __init__(self, type=None):
        """
        Stores the type passed to the checker
        """
        self.type = type

    def __call__(self, x):
        """
        Makes sure the argument is of the correct type (if set)
        """
        if self.type is None:
            return
        if not isinstance(x, self.type):
            raise TypeError(
                "Invalid type: Expected {}, got {}!".format(
                    self.type.__name__, type(x).__name__
                )
            )


class Range(TypeChecked):

    """
    Checks if an argument/return value is within a given input range.
    """

    def __init__(self, from_, to_, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.from_ = from_
        self.to_ = to_

    def __call__(self, x):
        super().__call__(x)
        return self.from_ <= x <= self.to_


class Positive(TypeChecked):

    """
    Checks if an argument/return value is positive.
    """

    def __call__(self, x):
        super().__call__(x)
        return x > 0


def check_defaults(annotations, defaults):
    """
    Checks if the default values.
    """
    for key, value in defaults.items():
        if key in annotations:
            validator = annotations[key]
            if callable(validator):
                if not isinstance(value, validator):
                    raise ValueError(
                        "Invalid default value for {}: {}".format(key, value)
                    )


def ValidateAnnotation(f):
    """
    Returns a decorator that performs the runtime checking.
    """
    annotations = {
        key: value() if inspect.isfunction(value) else value
        for key, value in f.__annotations__.items()
    }
    spec = inspect.getfullargspec(f)

    # todo - Change this Logic to properly populate the Deafult Values in Order
    defaultss = {}  # Not used
    # for i, x in enumerate(spec.args):
    # try:
    # defaultss[x]=spec.defaults[i]
    # except:
    # defaultss[x] = None

    if not spec.defaults is None:
        defaults = dict(zip(spec.args[-len(spec.defaults) :], spec.defaults))
        check_defaults(annotations, defaults)

    return_annotation = annotations.get("return")

    @functools.wraps(f)
    def check(*args, **kwargs):
        """
        Checks the arguments and the return value of function against
        the validators given in the annotations.
        """
        argdict = (
            defaults.copy()
        )  # this Dict Not having Non Default Data - Linked to fixing defaultss={}- Not used #todo
        argdict.update(dict(zip(spec.args, args)))
        argdict.update(kwargs)

        for key, annotation in annotations.items():
            if key == "return":
                continue
            value = argdict[key]
            try:
                if callable(annotation) and not annotation(value):
                    if (
                        value != False
                    ):  # workaround - If Value is False for bool -Skips Error - But Might also skip if Value is False for non-bools
                        raise ValueError("Invalid value for {}: {}".format(key, value))
            except:
                raise ValueError("Invalid value for {}: {}".format(key, value))
        rv = f(*args, **kwargs)
        if return_annotation and not return_annotation(rv):
            raise ValueError("Invalid return type: {}".format(rv))
        return rv

    check.tags = "meas"
    return check
