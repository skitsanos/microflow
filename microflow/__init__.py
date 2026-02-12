"""
Microflow: A lightweight workflow engine for Python
"""

__version__ = "0.1.0"
__author__ = "Microflow Team"

from .core.workflow import Workflow
from .core.runner import WorkflowRunner
from .core.task_spec import TaskSpec, Task, task
from .storage.json_store import JSONStateStore
from .storage.redis_store import RedisStateStore
from .queueing import (
    InMemoryWorkflowQueue,
    RedisWorkflowQueue,
    create_workflow_queue_from_env,
)

# Import built-in nodes
from .nodes.conditional import (
    if_node,
    switch_node,
    conditional_task,
    if_equals,
    if_greater_than,
    if_exists,
    switch_on_key,
)
from .nodes.http_request import (
    http_request,
    http_get,
    http_post,
    http_put,
    http_delete,
    webhook_call,
    rest_api_call,
    BearerAuth,
    BasicAuth,
    APIKeyAuth,
)
from .nodes.subworkflow import (
    subworkflow,
    parallel_subworkflows,
    workflow_chain,
    WorkflowLoader,
    load_workflow_from_file,
)
from .nodes.shell import shell_command, python_script, git_command, docker_command
from .nodes.file_ops import read_file, write_file, copy_file, move_file, list_directory
from .nodes.data_transform import (
    json_parse,
    json_stringify,
    csv_parse,
    data_filter,
    data_transform,
)
from .nodes.timing import delay, wait_until, wait_for_condition, rate_limit
from .nodes.notifications import send_email, slack_notification, simple_email
from .nodes.utilities import (
    validate_schema,
    template_render,
    batch,
    deduplicate,
    http_pagination,
    secret_read,
)
from .nodes.integrations import (
    db_query,
    db_exec,
    aql,
    cache_get,
    cache_set,
    s3_read,
    s3_write,
)
from .nodes.resilience import retry_policy, circuit_breaker, foreach
from .nodes.control_plane import (
    metrics_emit,
    trace_span,
    human_approval,
    queue_publish,
    queue_consume,
    idempotency_guard,
)
from .nodes.data_formats import (
    csv_read,
    csv_write,
    excel_read,
    excel_write,
    json_to_csv,
    csv_to_json,
    excel_to_json,
    read_csv_file,
    write_csv_file,
    read_excel_file,
    write_excel_file,
)

__all__ = [
    # Core components
    "Workflow",
    "WorkflowRunner",
    "task",
    "TaskSpec",
    "Task",
    "JSONStateStore",
    "RedisStateStore",
    "InMemoryWorkflowQueue",
    "RedisWorkflowQueue",
    "create_workflow_queue_from_env",
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
    # Shell/Process nodes
    "shell_command",
    "python_script",
    "git_command",
    "docker_command",
    # File operation nodes
    "read_file",
    "write_file",
    "copy_file",
    "move_file",
    "list_directory",
    # Data transformation nodes
    "json_parse",
    "json_stringify",
    "csv_parse",
    "data_filter",
    "data_transform",
    # Timing nodes
    "delay",
    "wait_until",
    "wait_for_condition",
    "rate_limit",
    # Notification nodes
    "send_email",
    "slack_notification",
    "simple_email",
    # Utility nodes
    "validate_schema",
    "template_render",
    "batch",
    "deduplicate",
    "http_pagination",
    "secret_read",
    # Integration nodes
    "db_query",
    "db_exec",
    "aql",
    "cache_get",
    "cache_set",
    "s3_read",
    "s3_write",
    # Resilience nodes
    "retry_policy",
    "circuit_breaker",
    "foreach",
    # Control-plane nodes
    "metrics_emit",
    "trace_span",
    "human_approval",
    "queue_publish",
    "queue_consume",
    "idempotency_guard",
    # Data format nodes
    "csv_read",
    "csv_write",
    "excel_read",
    "excel_write",
    "json_to_csv",
    "csv_to_json",
    "excel_to_json",
    "read_csv_file",
    "write_csv_file",
    "read_excel_file",
    "write_excel_file",
]
