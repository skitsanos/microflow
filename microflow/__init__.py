"""
Microflow: A lightweight workflow engine for Python
"""

__version__ = "0.1.0"
__author__ = "Microflow Team"

from .core.workflow import Workflow
from .core.task_spec import TaskSpec, Task, task
from .storage.json_store import JSONStateStore

# Import built-in nodes
from .nodes.conditional import (
    if_node, switch_node, conditional_task,
    if_equals, if_greater_than, if_exists, switch_on_key
)
from .nodes.http_request import (
    http_request, http_get, http_post, http_put, http_delete,
    webhook_call, rest_api_call,
    BearerAuth, BasicAuth, APIKeyAuth
)
from .nodes.subworkflow import (
    subworkflow, parallel_subworkflows, workflow_chain,
    WorkflowLoader, load_workflow_from_file
)

__all__ = [
    # Core components
    "Workflow",
    "task",
    "TaskSpec",
    "Task",
    "JSONStateStore",

    # Conditional nodes
    "if_node",
    "switch_node",
    "conditional_task",
    "if_equals",
    "if_greater_than",
    "if_exists",
    "switch_on_key",

    # HTTP nodes
    "http_request",
    "http_get",
    "http_post",
    "http_put",
    "http_delete",
    "webhook_call",
    "rest_api_call",
    "BearerAuth",
    "BasicAuth",
    "APIKeyAuth",

    # Sub-workflow nodes
    "subworkflow",
    "parallel_subworkflows",
    "workflow_chain",
    "WorkflowLoader",
    "load_workflow_from_file",
]