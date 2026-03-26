"""Safe expression evaluator that replaces unsafe eval() calls.

Uses ast.parse() + ast.walk() to whitelist safe AST node types,
rejecting anything that could lead to code execution exploits.
"""

import ast
import warnings
from typing import Any, Dict, Optional

# Safe built-in functions allowed in expressions
_SAFE_BUILTINS = {
    "len": len,
    "str": str,
    "int": int,
    "float": float,
    "bool": bool,
    "isinstance": isinstance,
    "dict": dict,
    "list": list,
    "tuple": tuple,
    "set": set,
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sum": sum,
    "sorted": sorted,
    "reversed": reversed,
    "enumerate": enumerate,
    "zip": zip,
    "range": range,
    "type": type,
    "hasattr": hasattr,
    "getattr": getattr,
    "True": True,
    "False": False,
    "None": None,
}

# AST node types that are considered safe
# Include deprecated types only if they still exist (removed in Python 3.14+)
_DEPRECATED_AST_TYPES: tuple = ()
for _name in ("Num", "Str", "NameConstant", "Index"):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        _cls = getattr(ast, _name, None)
        if _cls is not None:
            _DEPRECATED_AST_TYPES = (*_DEPRECATED_AST_TYPES, _cls)

_SAFE_NODE_TYPES = (
    # Literals and constants
    ast.Constant,
    *_DEPRECATED_AST_TYPES,
    ast.FormattedValue,
    ast.JoinedStr,
    # Collections
    ast.List,
    ast.Tuple,
    ast.Set,
    ast.Dict,
    # Expressions
    ast.Expression,
    ast.Expr,
    # Variables and attributes
    ast.Name,
    ast.Load,
    ast.Store,
    ast.Del,
    ast.Attribute,
    ast.Subscript,
    ast.Slice,
    # Operations
    ast.BinOp,
    ast.UnaryOp,
    ast.BoolOp,
    ast.Compare,
    # Operators
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
    ast.FloorDiv,
    ast.Mod,
    ast.Pow,
    ast.BitAnd,
    ast.BitOr,
    ast.BitXor,
    ast.LShift,
    ast.RShift,
    ast.Invert,
    ast.Not,
    ast.UAdd,
    ast.USub,
    ast.And,
    ast.Or,
    # Comparisons
    ast.Eq,
    ast.NotEq,
    ast.Lt,
    ast.LtE,
    ast.Gt,
    ast.GtE,
    ast.Is,
    ast.IsNot,
    ast.In,
    ast.NotIn,
    # Conditionals
    ast.IfExp,
    # Comprehensions
    ast.ListComp,
    ast.SetComp,
    ast.DictComp,
    ast.GeneratorExp,
    ast.comprehension,
    # Function calls (validated separately)
    ast.Call,
    ast.keyword,
    ast.Starred,
)

# Dangerous attribute names that must never be accessed
_FORBIDDEN_ATTRS = frozenset({
    "__class__",
    "__bases__",
    "__subclasses__",
    "__import__",
    "__builtins__",
    "__globals__",
    "__code__",
    "__closure__",
    "__func__",
    "__self__",
    "__module__",
    "__dict__",
    "__qualname__",
    "__init_subclass__",
    "__set_name__",
    "__reduce__",
    "__reduce_ex__",
    "__getattribute__",
    "__setattr__",
    "__delattr__",
    "__delete__",
    "__get__",
    "__set__",
    "__mro_entries__",
    "__init__",
    "__new__",
    "__del__",
    "mro",
})

# Dangerous names that must never be used as identifiers
_FORBIDDEN_NAMES = frozenset({
    "__import__",
    "__builtins__",
    "exec",
    "eval",
    "compile",
    "open",
    "breakpoint",
    "exit",
    "quit",
    "globals",
    "locals",
    "vars",
    "dir",
    "delattr",
    "setattr",
    "input",
    "memoryview",
    "help",
    "__build_class__",
    "__loader__",
    "__spec__",
})


def _validate_ast(tree: ast.AST) -> None:
    """Walk the AST and reject any unsafe node types or attribute accesses."""
    for node in ast.walk(tree):
        # Check node type is in whitelist
        # Suppress deprecation warnings from isinstance checks on deprecated AST types
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            is_safe = isinstance(node, _SAFE_NODE_TYPES)
        if not is_safe:
            raise ValueError(
                f"Unsafe expression: disallowed construct "
                f"'{type(node).__name__}'"
            )

        # Check variable names for forbidden identifiers
        if isinstance(node, ast.Name) and node.id in _FORBIDDEN_NAMES:
            raise ValueError(
                f"Unsafe expression: use of '{node.id}' is forbidden"
            )

        # Check attribute accesses for forbidden dunder names
        if isinstance(node, ast.Attribute):
            if node.attr in _FORBIDDEN_ATTRS:
                raise ValueError(
                    f"Unsafe expression: access to '{node.attr}' is forbidden"
                )

        # Check that function calls only use allowed functions
        if isinstance(node, ast.Call):
            func = node.func
            # Allow calls on Name (e.g. len(...), str(...))
            # Allow calls on Attribute (e.g. item.get(...), ctx.get(...))
            # The actual resolution happens at eval time; we just block
            # obviously dangerous patterns here.
            if isinstance(func, ast.Attribute) and func.attr in _FORBIDDEN_ATTRS:
                raise ValueError(
                    f"Unsafe expression: call to '{func.attr}' is forbidden"
                )

        # Block string values containing dunder patterns in constants
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            if any(attr in node.value for attr in
                   ("__class__", "__subclasses__", "__import__", "__builtins__", "__globals__")):
                raise ValueError(
                    "Unsafe expression: suspicious string constant detected"
                )


def safe_eval(
        expression: str,
        variables: Optional[Dict[str, Any]] = None,
        extra_builtins: Optional[Dict[str, Any]] = None,
) -> Any:
    """Safely evaluate a Python expression.

    Args:
        expression: The Python expression string to evaluate.
        variables: Mapping of variable names available in the expression
                   (e.g. {"ctx": ctx, "item": item}).
        extra_builtins: Additional safe callables to make available
                        (e.g. {"avg": my_avg_fn}).

    Returns:
        The result of evaluating the expression.

    Raises:
        ValueError: If the expression contains unsafe constructs.
        SyntaxError: If the expression is not valid Python.
    """
    if variables is None:
        variables = {}

    # Parse and validate the AST
    tree = ast.parse(expression, mode="eval")
    _validate_ast(tree)

    # Build the globals dict with safe builtins and user variables
    eval_globals: Dict[str, Any] = {"__builtins__": {}}
    eval_globals.update(_SAFE_BUILTINS)
    if extra_builtins:
        eval_globals.update(extra_builtins)
    eval_globals.update(variables)

    # Compile and evaluate
    code = compile(tree, "<safe_eval>", "eval")
    return eval(code, eval_globals)
