"""

Rules:

* Ignore reference counting
* Ignore failure cases, assume eval doesn't fail.
* Get minimal working version. But if implementing function
  try to include all functionality.
* Don't include fields that are not used.
"""
from __future__ import annotations

from typing import Generic, Type, TypeVar

from metadsl import Expression, expression
from metadsl_core import Boolean, Integer, Pair, Vec
from metadsl_rewrite import datatype_rule, default_rule, register

from .code import MCode

register_eval = register[__name__]


T = TypeVar("T")


class Unset(Expression, Generic[T]):
    """
    An unset value.
    """

    @classmethod
    def create(cls) -> T:
        ...


def unset(tp: Type[T]) -> T:
    return Unset[tp].create()  # type: ignore


class PyFrameObject(Expression, wrap_methods=True):
    pass


class PyThreadState(Expression, wrap_methods=True):
    @property
    def code(self) -> MCode:
        ...


class PyObject(Expression, wrap_methods=True):
    pass


class State(Expression):
    """
    State is a data type that represents a state of the program and external state.
    """


class _PyInterpreterFrame(Expression, wrap_methods=True):
    @classmethod
    def create(
        cls,
        f_funcobj: PyObject,
        f_globals: PyObject,
        f_builtins: PyObject,
        f_locals: PyObject,
        f_code: MCode,
        frame_obk: PyFrameObject,
        previous: _PyInterpreterFrame,
        prev_instr: Integer,
        stacktop: Integer,
        is_entry: Boolean,
        owner: Integer,
        localsplus: Vec[PyObject],
    ) -> _PyInterpreterFrame:
        ...

    @property
    def f_funcobj(self) -> PyObject:
        ...

    @property
    def f_globals(self) -> PyObject:
        ...

    @property
    def f_builtins(self) -> PyObject:
        ...

    @property
    def f_locals(self) -> PyObject:
        ...

    @property
    def f_code(self) -> MCode:
        ...

    @property
    def frame_obk(self) -> PyFrameObject:
        ...

    @property
    def previous(self) -> _PyInterpreterFrame:
        ...

    @property
    def prev_instr(self) -> Integer:
        ...

    @property
    def stacktop(self) -> Integer:
        ...

    @property
    def is_entry(self) -> Boolean:
        ...

    @property
    def owner(self) -> Integer:
        ...


register_eval(datatype_rule(_PyInterpreterFrame))


class PyFunctionObject(Expression, wrap_methods=True):
    @property
    def code(self) -> MCode:
        ...


# TODO: Create update with varargs!


@expression
def _PyEval_Vector(
    state: State,
    tstate: PyThreadState,
    func: PyFunctionObject,
    locals: Vec[PyObject],
    args: Vec[PyObject],
    argcount: Integer,
    kwnames: Vec[PyObject],
) -> Pair[State, PyObject]:
    """
    Evaluate a code object in a frame.
    """
    state, frame = _PyEvalFramePushAndInit(
        state, tstate, func, locals, args, argcount, kwnames
    ).spread
    # TODO
    # retval = _PyEval_EvalFrame(state, tstate, frame, Integer.from_int(0))

    # _PyEvalFrameClearAndPop(tstate, frame)
    # return retval;
    # # f = _PyEvalFramePushAndInit(state, tstate, con, locals, args, argcount, kwnames)

    # # _coro = make_coro(state, con, f)
    # # _other = _PyEval_EvalFrame(state, tstate, f, 0)
    # # return tstate.code.type.type.match(
    # #     generator=_coro,
    # #     coroutine=_coro,
    # #     async_generator=_coro,
    # #     normal=_other,
    # # )


register_eval(default_rule(_PyEval_Vector))


def _PyEvalFramePushAndInit(
    state: State,
    tstate: PyThreadState,
    func: PyFunctionObject,
    locals: Vec[PyObject],
    args: Vec[PyObject],
    argcount: Integer,
    kwnames: Vec[PyObject],
) -> Pair[State, _PyInterpreterFrame]:
    """
    Push a new frame and initialize it.
    """
    frame = _PyThreadState_PushFrame(tstate, get_code_framesize(func.code))
    frame = _PyFrame_InitializeSpecials(frame, func, locals, args, argcount, kwnames)
    # _PyFrame_InitializeSpecials(frame, func, locals, code);
    # PyObject **localsarray = &frame->localsplus[0];
    # for (int i = 0; i < code->co_nlocalsplus; i++) {
    #     localsarray[i] = NULL;
    # }
    # if (initialize_locals(tstate, func, localsarray, args, argcount, kwnames)) {
    #     assert(frame->owner != FRAME_OWNED_BY_GENERATOR);
    #     _PyEvalFrameClearAndPop(tstate, frame);
    #     return NULL;
    # }
    # return frame;


register_eval(default_rule(_PyEvalFramePushAndInit))


@expression
def _PyFrame_InitializeSpecials(
    frame: _PyInterpreterFrame,
    func: PyFunctionObject,
    locals: Vec[PyObject],
    code: MCode,
) -> _PyInterpreterFrame:
    """
    Initialize the special variables in a frame.
    """


#     frame->f_funcobj = (PyObject *)func;
#     frame->f_code = (PyCodeObject *)Py_NewRef(code);
#     frame->f_builtins = func->func_builtins;
#     frame->f_globals = func->func_globals;
#     frame->f_locals = locals;
#     frame->stacktop = code->co_nlocalsplus;
#     frame->frame_obj = NULL;
#     frame->prev_instr = _PyCode_CODE(code) - 1;
#     frame->is_entry = false;
#     frame->owner = FRAME_OWNED_BY_THREAD;
# }


register_eval(default_rule(_PyFrame_InitializeSpecials))


# typedef struct _PyInterpreterFrame {
#     /* "Specials" section */
#     PyObject *f_funcobj; /* Strong reference */
#     PyObject *f_globals; /* Borrowed reference */
#     PyObject *f_builtins; /* Borrowed reference */
#     PyObject *f_locals; /* Strong reference, may be NULL */
#     PyCodeObject *f_code; /* Strong reference */
#     PyFrameObject *frame_obj; /* Strong reference, may be NULL */
#     /* Linkage section */
#     struct _PyInterpreterFrame *previous;
#     // NOTE: This is not necessarily the last instruction started in the given
#     // frame. Rather, it is the code unit *prior to* the *next* instruction. For
#     // example, it may be an inline CACHE entry, an instruction we just jumped
#     // over, or (in the case of a newly-created frame) a totally invalid value:
#     _Py_CODEUNIT *prev_instr;
#     int stacktop;     /* Offset of TOS from localsplus  */
#     bool is_entry;  // Whether this is the "root" frame for the current _PyCFrame.
#     char owner;
#     /* Locals and stack */
#     PyObject *localsplus[1];
# } _PyInterpreterFrame;


# TODO: Add update method to dataclasses instead of each setter?


@expression
def _PyThreadState_PushFrame(
    tstate: PyThreadState, size: Integer
) -> _PyInterpreterFrame:
    """
    Push a frame onto the thread state stack.
    """
    # this does nothing in our symbolic interpreter, only allocates memory
    return _PyInterpreterFrame.create(
        unset(PyObject),
        unset(PyObject),
        unset(PyObject),
        unset(PyObject),
        unset(MCode),
        unset(PyFrameObject),
        unset(_PyInterpreterFrame),
        unset(Integer),
        unset(Integer),
        unset(Boolean),
        unset(Integer),
        unset(Vec[PyObject]),
    )


register_eval(default_rule(_PyThreadState_PushFrame))


@expression
def get_code_framesize(code: MCode) -> Integer:
    """
    Get the size of the frame for a code object. co_framesize
    """
    ...


# @expression
# def _PyEval_MakeFrameVector(
#     state: State,
#     tstate: PyThreadState,
#     con: PyFrameConstructor,
#     locals: PyObject,
#     args: PyObject,
#     argcount: Integer,
#     kwnames: PyObject,
# ) -> PyFrameObject:
# TODO:
# co = con.code
# co_args = co.type.args_
# total_args = co_args.positional_only.length + co_args.keyword_only.length + co_args.positional_or_keyword.length
# f = _PyFrame_New_NoTrack(state, tstate, con, locals)


# # TODO: Create PyFrameObject dataclass from frameobject.h
# @expression
# def _PyFrame_New_NoTrack(
#     state: State,
#     tstate: PyThreadState,
#     con: PyFrameConstructor,
#     locals: PyObject,
# ) -> PyFrameObject:
#     # TODO
#     ...

# @expression
# def _PyEval_EvalFrame(
#     state: State,
#     tstate: PyThreadState,
#     f: PyFrameObject,
#     throwflag: Integer,
# ) -> PyObject:
#     """
#     Evaluate a frame until it returns.
#     """
#     #TODO

#     ...

# @expression
# def make_coro(state: State, con: PyFrameConstructor, f: PyFrameObject) -> PyObject:
#     # TODO
#     ...
