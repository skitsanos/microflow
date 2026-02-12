"""Task specification and Task classes for workflow engine"""

from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Optional, Set, Union


@dataclass
class TaskSpec:
    """Specification for a workflow task"""

    fn: Union[Callable[..., Awaitable[Any]], Callable[..., Any]]
    name: str
    max_retries: int = 0
    backoff_s: float = 0.0
    timeout_s: Optional[float] = None
    tags: Set[str] = field(default_factory=set)
    description: str = ""


class Task:
    """A workflow task with dependencies"""

    def __init__(self, spec: TaskSpec):
        self.spec = spec
        self.downstream: Set["Task"] = set()
        self.upstream: Set["Task"] = set()

    def __rshift__(self, other: "Task") -> "Task":
        """Define task dependency using >> operator"""
        self.downstream.add(other)
        other.upstream.add(self)
        return other

    def __repr__(self) -> str:
        return f"Task(name='{self.spec.name}')"


def task(
    name: Optional[str] = None,
    max_retries: int = 0,
    backoff_s: float = 0.0,
    timeout_s: Optional[float] = None,
    tags: Optional[Set[str]] = None,
    description: str = "",
) -> Callable:
    """Decorator to create a workflow task"""

    def decorator(fn: Union[Callable[..., Awaitable[Any]], Callable[..., Any]]) -> Task:
        spec = TaskSpec(
            fn=fn,
            name=name or fn.__name__,
            max_retries=max_retries,
            backoff_s=backoff_s,
            timeout_s=timeout_s,
            tags=tags or set(),
            description=description,
        )
        return Task(spec)

    return decorator
