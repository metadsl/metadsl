# Notes on Python

## CPython Code Execution Entrypoints

What are the ways that CPython code can be executed? Here are some entrypoints
with the tracebacks for code exection (found by setting breakpoints and triggering
these all...):

1. `eval(...)`
    1. `_PyEval_EvalFrameDefault`
    2. `_PyEval_EvalFrame`
    3. `_PyEval_Vector`
    4. `PyEval_EvalCode`
    5. `run_eval_code_obj`
    6. `run_mod`
    7. `PyRun_StringFlags`
    8. `builtin_eval_impl`
    9. `builtin_eval`
    10. `cfunction_vectorcall_FASTCALL`
    11. ...
2. `exec(...)`
    1. `_PyEval_EvalFrameDefault`
    2. `_PyEval_EvalFrame`
    3. `_PyEval_Vector`
    4. `PyEval_EvalCode`
    5. `run_eval_code_obj`
    6. `run_mod`
    7. `PyRun_StringFlags`
    5. `builtin_exec_impl`
    6. `builtin_exec`
    7. `cfunction_vectorcall_FASTCALL`
    8. ...
3. `python file.py`
    1. `_PyEval_EvalFrameDefault`
    2. `_PyEval_EvalFrame`
    3. `_PyEval_Vector`
    4. `PyEval_EvalCode`
    5. `run_eval_code_obj`
    6. `run_mod`
    7. `pyrun_file`
    8. `_PyRun_SimpleFileObject`
    9. `_PyRun_AnyFileObject`
    10. `pymain_run_file_obj`
    11. ...
4. `python -m module`
    1. `_PyEval_EvalFrameDefault`
    2. `_PyEval_EvalFrame`
    3. `_PyEval_Vector`
    4. `PyEval_EvalCode`
    5. `builtin_exec_impl`
    6. `builtin_exec`
    7. `cfunction_vectorcall_FASTCALL`
    8. ...
    9 `PyObject_Call`
    10. `pymain_run_module`
    11. ...
5. `python -c "code"`
    1. `_PyEval_EvalFrameDefault`
    2. `_PyEval_EvalFrame`
    3. `_PyEval_Vector`
    4. `PyEval_EvalCode`
    5. `run_eval_code_obj`
    6. `run_mod`
    7. `PyRun_StringFlags`
    8. ...
6. python interpreter
    1. `_PyEval_EvalFrameDefault`
    2. `_PyEval_EvalFrame`
    3. `_PyEval_Vector`
    4. `PyEval_EvalCode`
    5. `run_eval_code_obj`
    6. `run_mod`
    7. `pyrun_file`
    8. `_PyRun_SimpleFileObject`
    9. `_PyRun_AnyFileObject`
    10. `PyRun_AnyFileExFlags`
    11. `pymain_run_stdin`
    12. ...
7. Function call
    1. `_PyEval_EvalFrameDefault`
    2. `_PyEval_EvalFrame`
    3. `_PyEval_Vector`
    4. `_PyFunction_Vectorcall`
    5. `builtin___build_class__`
    6. `cfunction_vectorcall_FASTCALL_KEYWORDS`
    7. ...
8. TODO: `gen_send_ex2` for generators calls `_PyEval_EvalFrame` as well


Now what we can think about is which function to recreate in metadsl in order
to do symbolic execution of CPython. One common denominator is `_PyEval_Vector`
so lets try to replicate this function in metadsl...