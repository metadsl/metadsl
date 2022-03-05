
from __future__ import annotations
import typing
from metadsl import *
from metadsl_rewrite import *

from .strategies import *
from .mapping import *

__all__ = ["State", "line", "get_lines"]

class State(Expression):
    @expression
    @classmethod
    def create(
        cls,
        namespace: Mapping[str, object], 
        fs: Mapping[str, bytes],
        artifacts: Mapping[str, object],
    ) -> State:
        ...
    
    @expression #type: ignore
    @property
    def namespace(self) ->  Mapping[str, object]:
        ...

    @expression#type: ignore
    @property
    def fs(self) ->  Mapping[str, bytes]:
        ...

    @expression#type: ignore
    @property
    def artifacts(self) ->  Mapping[str, object]:
        ...

    @expression
    def replace(
        self,
        namespace: typing.Union[Mapping[str, object], None]=None, 
        fs: typing.Union[Mapping[str, bytes], None]=None,
        artifacts: typing.Union[Mapping[str, object], None]=None,
    ) -> State:
        ...
    
    @expression
    @classmethod
    def empty(cls) -> State:
        return cls.create(
            Mapping[str, object].empty(),
            Mapping[str, bytes].empty(),
            Mapping[str, object].empty()
        )

    # @expression
    def set_var(self, k: str, v: object) -> State:
        return self.replace(
            namespace=self.namespace.setitem(k, v)
        )

    # @expression
    def get_var(self, k: str) -> object:
        return self.namespace[k]

register_ds(default_rule(State.empty))     
# register_ds(default_rule(State.get_var))     
# register_ds(default_rule(State.set_var))     

@register_ds
@rule
def state_rules(
    state: State,

    namespace: Mapping[str, object], 
    fs: Mapping[str, bytes],
    artifacts: Mapping[str, object],
    
    new_namespace: typing.Union[Mapping[str, object], None], 
    new_fs: typing.Union[Mapping[str, bytes], None],
    new_artifacts: typing.Union[Mapping[str, object], None],

    old_namespace: typing.Union[Mapping[str, object], None], 
    old_fs: typing.Union[Mapping[str, bytes], None],
    old_artifacts: typing.Union[Mapping[str, object], None],
):
    created = State.create(namespace, fs, artifacts)
    
    yield created.artifacts, artifacts
    yield created.namespace, namespace
    yield created.fs, fs
    
    def created_replace_result():
        return State.create(
            new_namespace or namespace,
            new_fs or fs,
            new_artifacts or artifacts
        )
        
    yield created.replace(new_namespace, new_fs, new_artifacts), created_replace_result

    def replace_replace_result():
        return state.replace(
            new_namespace or old_namespace,
            new_fs or old_fs,
            new_artifacts or old_artifacts
        )
        
    yield state.replace(old_namespace, old_fs, old_artifacts).replace(new_namespace, new_fs, new_artifacts), replace_replace_result

    # Getting an property can grab it from the replaced
    yield state.replace(namespace).namespace, namespace
    yield state.replace(fs).fs, fs
    yield state.replace(artifacts).artifacts, artifacts

T = typing.TypeVar("T")

@expression
def line(line: int, o: T) -> T:
    ...


def get_lines(x: object) -> set[int]:
    if not isinstance(x, Expression):
        return set()


    if x.function == line:
        lines = {typing.cast(int, x.args[0])}
    else:
        lines = get_lines(x.function)
    
    for arg in x.args:
        lines |= get_lines(arg)
    
    for _, v in x.kwargs.items():
        lines |= get_lines(v)
    
    return lines



