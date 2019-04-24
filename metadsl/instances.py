# import dataclasses
# import typing

# from .expressions import Call

# __all__ = ["Instance", "InstanceType", "instance_type"]


# Instance_ = typing.TypeVar("Instance_", bound="Instance")


# @dataclasses.dataclass
# class Instance:
#     __call__: Call

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
#     type: typing.Type[Instance_]
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
