"""Abstract syntax tree nodes for RANCAGE 0.1 and 0.2."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any

@dataclass(frozen=True)
class Span:
    line: int
    column: int

@dataclass
class FieldDecl:
    name: str
    type_name: str
    span: Span

@dataclass
class RecordDecl:
    name: str
    fields: list[FieldDecl]
    span: Span

@dataclass
class Program:
    functions: list[Function]
    module: str = "main"
    records: list[RecordDecl] = field(default_factory=list)

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
class FieldAssign(Stmt):
    target: Expr
    field: str
    value: Expr
    span: Span

@dataclass
class IndexAssign(Stmt):
    target: Expr
    index: Expr
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

class Expr:
    inferred_type: str | None = None

@dataclass
class Literal(Expr):
    value: Any
    type_name: str
    span: Span

@dataclass
class NullLiteral(Expr):
    span: Span
    value: Any = None
    type_name: str = "null"

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

@dataclass
class FieldAccess(Expr):
    target: Expr
    field: str
    span: Span

@dataclass
class IndexExpr(Expr):
    target: Expr
    index: Expr
    span: Span

@dataclass
class ListLiteral(Expr):
    elements: list[Expr]
    span: Span

@dataclass
class FieldInit:
    name: str
    value: Expr
    span: Span

@dataclass
class RecordInit(Expr):
    name: str
    fields: list[FieldInit]
    span: Span

@dataclass
class MapLiteral(Expr):
    entries: list[tuple[Expr, Expr]]
    span: Span
