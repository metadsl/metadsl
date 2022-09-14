from __future__ import annotations

from types import CodeType

from metadsl import Expression, expression
from metadsl_core import Abstraction, Either, Integer, Maybe, Pair
from metadsl_core.boolean import Boolean
from metadsl_rewrite import R, default_rule, register, rule

register_eval = register[__name__]


@expression
def _PyEval_Vector(
    state: State,
    tstate: PyThreadState,
    con: PyFrameConstructor,
    locals: PyObject,
    args: PyObject,
    argcount: Integer,
    kwnames: PyObject,
) -> PyObject:
    """
    Evaluate a code object in a frame.
    """
    f = _PyEval_MakeFrameVector(state, tstate, con, locals, args, argcount, kwnames)

    if code
    # This is a corootuine if it has a function type and that type is a coroutine type.
    is_coro = tstate.code.type.match(
        Boolean.false,
        Abstraction[FunctionCodeType, Boolean].from_fn(lambda fct: fct.type.is_coro),
    )

    return is_coro.if_(make_coro(state, con, f), _PyEval_EvalFrame(state, tstate, f, 0))


register_eval(default_rule(_PyEval_Vector))


@expression
def _PyEval_MakeFrameVector(
    state: State,
    tstate: PyThreadState,
    con: PyFrameConstructor,
    locals: PyObject,
    args: PyObject,
    argcount: Integer,
    kwnames: PyObject,
) -> PyFrameObject:
    co = con.code
    total_args = co.type.match(
        Integer.from_int(0),
        # TODO: Add ability to get total number of args from code object args.
        Abstraction[FunctionCodeType, Integer].from_fn(lambda fct: fct.args.),
    )

@expression
def make_coro(state: State, con: PyFrameConstructor, f: PyFrameObject) -> PyObject:
    # TODO
    ...

class PyFrameObject(Expression):
    pass

class PyThreadState(Expression):
    @expression
    @property
    def code(self) -> CodeType:
        ...


class PyFrameConstructor(Expression):
    
    # TODO
    @expression
    @property
    def code(self) -> CodeType:
        ...


class PyObject(Expression):
    pass


class Object(Expression):
    pass


class State(Expression):
    """
    State is a data type that represents a state of the program and external state.
    """
