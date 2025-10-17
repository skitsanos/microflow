"""Built-in node types for Microflow workflows"""

from .conditional import if_node, switch_node, conditional_task
from .http_request import http_request, http_get, http_post, webhook_call
from .subworkflow import subworkflow, parallel_subworkflows
from .shell import shell_command, python_script, git_command, docker_command
from .file_ops import read_file, write_file, copy_file, move_file, list_directory
from .data_transform import json_parse, json_stringify, csv_parse, data_filter, data_transform
from .timing import delay, wait_until, wait_for_condition, rate_limit
from .notifications import send_email, slack_notification, simple_email

__all__ = [
    # Conditional nodes
    "if_node",
    "switch_node",
    "conditional_task",

    # HTTP nodes
    "http_request",
    "http_get",
    "http_post",
    "webhook_call",

    # Sub-workflow nodes
    "subworkflow",
    "parallel_subworkflows",

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
]