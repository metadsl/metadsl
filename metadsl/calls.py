import dataclasses
import typing
import functools

ArgType = typing.TypeVar("ArgType")
ReturnType = typing.TypeVar("ReturnType")
NewArgType = typing.TypeVar("NewArgType")

__all__ = ["call", "Call", "Instance"]


@dataclasses.dataclass
class Call(typing.Generic[ArgType, ReturnType]):
    function: typing.Callable[..., ReturnType]
    args: typing.Tuple[ArgType, ...]

    def __str__(self):
        return f"{self.function.__name__}({', '.join(map(str, self.args))})"

    def __repr__(self):
        return f"Call({self.function.__name__}, {self.args})"


T_Callable = typing.TypeVar("T_Callable", bound=typing.Callable)


def call(
    type_fn: typing.Callable[..., typing.Callable[[Call], typing.Any]]
) -> typing.Callable[[T_Callable], T_Callable]:
    """
    Creates a Call object by wrapping a Python function and providing a function
    that will take in a call and return the proper return type
    """

    def inner(fn: T_Callable, type_fn=type_fn) -> T_Callable:
        # copy name and docstring from original function
        @functools.wraps(fn)
        def inner_inner(*args, type_fn=type_fn):
            return type_fn(*args)(Call(inner_inner, args))

        return typing.cast(T_Callable, inner_inner)

    return inner


@dataclasses.dataclass
class Instance:
    # This should have a ReturnType of self, but we can't type this properly
    # because we don't have access to the self type a property
    _call: Call


#     @property
#     def __type__(self: Instance_) -> "InstanceType[Instance_]":
#         fields = tuple(
#             getattr(self, field.name)
#             for field in dataclasses.fields(self)
#             if field.name != "__value__"
#         )
#         return InstanceType(type(self), fields)

#     def __repr__(self):
#         return f"{repr(self.__type__)}({repr(self.__call__)})"


# @dataclasses.dataclass
# class InstanceType(typing.Generic[Instance_]):
#     _type_: typing.Type[Instance_]
#     args: typing.Tuple

#     def __call__(self, value: object) -> Instance_:
#         return self.type(value, *self.args)  # type: ignore

#     def __repr__(self):
#         name = self.type.__name__
#         if not self.args:
#             return name
#         return f"{name}[{', '.join(repr(arg) for arg in self.args)}]"


# def instance_type(type: typing.Type[Instance_], *args) -> InstanceType[Instance_]:
#     return InstanceType(type, args)
