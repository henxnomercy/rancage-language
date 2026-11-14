"""Abstract syntax tree nodes for RANCAGE 0.1."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class Span:
    line: int
    column: int

@dataclass
class Program:
    functions: list[Function]
    module: str = "main"

@dataclass
class Param:
    name: str
    type_name: str
    span: Span

@dataclass
class Function:
    name: str
    params: list[Param]
    return_type: str
    body: list[Stmt]
    span: Span

class Stmt: pass

@dataclass
class Let(Stmt):
    name: str
    type_name: str | None
    value: Expr
    is_const: bool
    span: Span

@dataclass
class Assign(Stmt):
    name: str
    value: Expr
    span: Span

@dataclass
class Return(Stmt):
    value: Expr | None
    span: Span

@dataclass
class ExprStmt(Stmt):
    value: Expr
    span: Span

@dataclass
class If(Stmt):
    condition: Expr
    then_body: list[Stmt]
    else_body: list[Stmt] | None
    span: Span

@dataclass
class While(Stmt):
    condition: Expr
    body: list[Stmt]
    span: Span

class Expr: pass

@dataclass
class Literal(Expr):
    value: Any
    type_name: str
    span: Span

@dataclass
class Name(Expr):
    value: str
    span: Span

@dataclass
class Unary(Expr):
    op: str
    operand: Expr
    span: Span

@dataclass
class Binary(Expr):
    left: Expr
    op: str
    right: Expr
    span: Span

@dataclass
class Call(Expr):
    name: str
    args: list[Expr]
    span: Span
