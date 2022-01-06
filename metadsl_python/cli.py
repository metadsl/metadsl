import argparse
from os import linesep
import pathlib
from types import CodeType
from rich.syntax import Syntax
import importlib.util
from typing import Optional, cast
import dis
from metadsl_python.code_data import CodeData

parser = argparse.ArgumentParser(description="Inspect Python code objects.")
parser.add_argument("file", type=pathlib.Path, nargs="?", help="path to Python program")
parser.add_argument("-c", type=str, help="program passed in as string", metavar="cmd")
parser.add_argument(
    "-e", type=str, help="string evalled to make program", metavar="eval"
)
parser.add_argument("-m", type=str, help="python library", metavar="mod")
parser.add_argument("--dis", action="store_true", help="print Python's dis analysis")
parser.add_argument("--source", action="store_true", help="print the source code")

if __name__ == "__main__":
    from rich.console import Console

    args = parser.parse_args()
    file, cmd, mod, eval_, show_dis, show_source = (
        args.file,
        args.c,
        args.m,
        args.e,
        args.dis,
        args.source,
    )

    if len(list(filter(None, [file, cmd, mod, eval_]))) != 1:
        parser.error("Must specify exactly one of file, cmd, eval, or mod")

    console = Console()
    source: Optional[str]
    code: CodeType
    if eval_ is not None:
        source = eval(eval_, {"linesep": linesep})
        code = compile(cast(str, source), "<string>", "exec")
    elif file is not None:
        source = file.read_text()
        code = compile(cast(str, source), str(file), "exec")
    elif cmd is not None:
        # replace escaped newlines with newlines
        source = cmd.replace("\\n", "\n")
        code = compile(source, "<string>", "exec")  # type: ignore
    elif mod is not None:
        spec = importlib.util.find_spec(mod)
        assert spec
        assert spec.loader
        code = spec.loader.get_code(mod)  # type: ignore
        source = spec.loader.get_source(mod)  # type: ignore
        assert code

    if show_source and source is not None:
        console.print(Syntax(source, "python", line_numbers=True))
    if show_dis:
        dis.dis(code)
    code_data = CodeData.from_code(code)
    console.print(code_data)
