from dataclasses import _FIELDS, Field  # type: ignore
from copy import copy


class DataclassHideDefault:
    """
    Inherit from this class when creating a dataclass to not show any fields
    in the repr which are set to their default.

    This lets us control the rich output for dataclasses, since it looks
    at the `repr` of each field to know whether to display it.
    """

    def __getattribute__(self, __name: str) -> object:
        res = super().__getattribute__(__name)
        # If we are getting the dataclass fields attribute
        if __name == _FIELDS:
            # Then return the same fields, however changing any field which
            # is set to the default to not show in the repr
            return {
                name: set_repr_false(field)
                if field.default == getattr(self, name)
                else field
                for name, field in res.items()
            }
            # Transform fields
        return res


def set_repr_false(field: Field) -> Field:
    # Copy the field first, so that only this instance is mutated
    new_field = copy(field)
    new_field.repr = False
    return new_field
