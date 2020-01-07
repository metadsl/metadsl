"""
Compile LLVM module from IR.
"""
from __future__ import annotations
import typing

from metadsl import *
from metadsl_core import *
import llvmlite.binding as binding

__all__ = ["ModuleRef", "ExecutionEngine", "llvmlite_binding_rules"]

binding.initialize()
binding.initialize_native_target()
binding.initialize_native_asmprinter()
target_machine = binding.Target.from_default_triple().create_target_machine()


llvmlite_binding_rules = RulesRepeatFold()
register_llvmlite_binding = llvmlite_binding_rules.append


class ModuleRef(Expression):
    @expression
    @classmethod
    def create(cls, code: str) -> ModuleRef:
        ...

    @expression
    def optimize(self, level: int) -> ModuleRef:
        ...

    @expression
    @classmethod
    def box(cls, mod: binding.ModuleRef) -> ModuleRef:
        ...


@register_llvmlite_binding
@rule
def module_ref_create(code: str) -> R[ModuleRef]:
    def inner() -> ModuleRef:
        llmod = binding.parse_assembly(code)
        llmod.verify()
        return ModuleRef.box(llmod)

    return ModuleRef.create(code), inner


@register_llvmlite_binding
@rule
def module_ref_optimize(mod: binding.ModuleRef, level: int) -> R[ModuleRef]:
    def inner() -> ModuleRef:
        pmb = binding.create_pass_manager_builder()
        pmb.opt_level = level
        pm = binding.create_module_pass_manager()
        pmb.populate(pm)
        pm.run(mod)
        return ModuleRef.box(mod)

    return ModuleRef.box(mod).optimize(level), inner


class ExecutionEngine(Expression):
    @expression
    @classmethod
    def create(cls, mod: ModuleRef) -> ExecutionEngine:
        ...

    @expression
    @classmethod
    def box(cls, engine: binding.ExecutionEngine) -> ExecutionEngine:
        ...

    @expression
    def get_function_address(self, name: str) -> int:
        ...


# keep a global mapping of these so they dont get GCed
_execution_engines: typing.List[binding.ExecutionEngine] = []


@register_llvmlite_binding
@rule
def execution_engine_create(mod: binding.ModuleRef) -> R[ExecutionEngine]:
    def inner() -> ExecutionEngine:
        ee = binding.create_mcjit_compiler(mod, target_machine)
        ee.finalize_object()
        _execution_engines.append(ee)
        return ExecutionEngine.box(ee)

    return ExecutionEngine.create(ModuleRef.box(mod)), inner


@register_llvmlite_binding
@rule
def execution_engine_address(engine: binding.ExecutionEngine, name: str) -> R[int]:
    return (
        ExecutionEngine.box(engine).get_function_address(name),
        lambda: engine.get_function_address(name),
    )
