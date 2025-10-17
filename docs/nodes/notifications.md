# Notification Nodes

Notification nodes enable your workflows to send alerts, messages, and notifications through various channels including email and Slack. They're essential for keeping stakeholders informed about workflow status and results.

## Available Nodes

### send_email

Send rich HTML/text emails with attachments and flexible configuration.

**Parameters:**
- `to` (Union[str, List[str]]): Recipient email address(es)
- `subject` (str): Email subject line
- `body` (str): Email body content
- `from_email` (str, optional): Sender email address
- `cc` (Union[str, List[str]], optional): CC recipients
- `bcc` (Union[str, List[str]], optional): BCC recipients
- `attachments` (List[str], optional): List of file paths to attach
- `html` (bool): Whether body is HTML (default: False)
- `smtp_server` (str): SMTP server hostname (default: "localhost")
- `smtp_port` (int): SMTP server port (default: 587)
- `smtp_username` (str, optional): SMTP authentication username
- `smtp_password` (str, optional): SMTP authentication password
- `use_tls` (bool): Whether to use TLS encryption (default: True)
- `name` (str, optional): Node name

**Returns:**
- `email_success`: Boolean indicating if email was sent successfully
- `email_recipients`: List of all recipients (to, cc, bcc)
- `email_subject`: The subject that was sent
- `email_size`: Size of email in bytes
- `email_error`: Error message if sending failed

**Example:**
```python
from microflow import send_email, task

@task(name="prepare_report")
def prepare_report(ctx):
    return {
        "report_data": "Daily processing completed with 150 items processed.",
        "recipient_email": "manager@company.com"
    }

# Send detailed email
daily_report_email = send_email(
    to="{{ctx.recipient_email}}",
    subject="Daily Processing Report - {{ctx.current_date}}",
    body="""
    <h2>Daily Report</h2>
    <p>{{ctx.report_data}}</p>
    <p>Report generated at: {{ctx.timestamp}}</p>
    """,
    from_email="workflows@company.com",
    html=True,
    smtp_server="smtp.company.com",
    smtp_port=587,
    smtp_username="workflow_bot",
    smtp_password="secure_password",
    use_tls=True,
    name="send_daily_report"
)

prepare_report >> daily_report_email
```

### slack_notification

Send notifications to Slack channels or users.

**Parameters:**
- `webhook_url` (str): Slack webhook URL
- `message` (str): Message content
- `channel` (str, optional): Channel to send to (if webhook supports it)
- `username` (str, optional): Bot username to display
- `icon_emoji` (str, optional): Emoji icon for bot
- `attachments` (List[Dict], optional): Slack message attachments
- `blocks` (List[Dict], optional): Slack block kit elements
- `name` (str, optional): Node name

**Returns:**
- `slack_success`: Boolean indicating if message was sent successfully
- `slack_channel`: Channel the message was sent to
- `slack_message`: The message that was sent
- `slack_response`: Response from Slack API
- `slack_error`: Error message if sending failed

**Example:**
```python
from microflow import slack_notification, task

@task(name="prepare_slack_data")
def prepare_slack_data(ctx):
    return {
        "workflow_status": "completed",
        "items_processed": 42,
        "execution_time": "2.5 seconds"
    }

# Simple Slack notification
simple_slack = slack_notification(
    webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
    message="Workflow completed successfully! Processed {{ctx.items_processed}} items.",
    channel="#workflows",
    username="WorkflowBot",
    icon_emoji=":robot_face:",
    name="workflow_completion_alert"
)

# Rich Slack notification with attachments
rich_slack = slack_notification(
    webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
    message="Workflow Status Update",
    attachments=[
        {
            "color": "good",
            "title": "Processing Complete",
            "fields": [
                {"title": "Status", "value": "{{ctx.workflow_status}}", "short": True},
                {"title": "Items", "value": "{{ctx.items_processed}}", "short": True},
                {"title": "Duration", "value": "{{ctx.execution_time}}", "short": True}
            ],
            "footer": "Microflow Automation",
            "ts": "{{ctx.timestamp}}"
        }
    ],
    name="detailed_slack_report"
)

prepare_slack_data >> simple_slack
prepare_slack_data >> rich_slack
```

### simple_email

Simplified email sending for basic notifications.

**Parameters:**
- `to` (str): Recipient email address
- `subject` (str): Email subject
- `message` (str): Email message
- `name` (str, optional): Node name

**Returns:**
- `email_success`: Boolean indicating if email was sent
- `email_recipient`: The recipient address
- `email_subject`: The subject that was sent
- `email_error`: Error message if sending failed

**Example:**
```python
from microflow import simple_email

# Quick notification email
alert_email = simple_email(
    to="admin@company.com",
    subject="Workflow Alert: High Priority",
    message="The critical data processing workflow has completed with warnings. Please review the logs.",
    name="critical_alert"
)
```

## Advanced Usage

### Dynamic Email Content

Build email content dynamically from workflow context:

```python
from microflow import task, send_email

@task(name="generate_email_content")
def generate_email_content(ctx):
    results = ctx.get("processing_results", {})
    errors = ctx.get("error_list", [])

    # Build HTML email body
    html_body = f"""
    <html>
    <body>
        <h2>Workflow Execution Report</h2>
        <h3>Summary</h3>
        <ul>
            <li>Total Items: {results.get('total', 0)}</li>
            <li>Successful: {results.get('success', 0)}</li>
            <li>Failed: {results.get('failed', 0)}</li>
        </ul>

        {"<h3>Errors</h3><ul>" + "".join(f"<li>{error}</li>" for error in errors) + "</ul>" if errors else ""}

        <p><em>Generated by Microflow at {ctx.get('timestamp')}</em></p>
    </body>
    </html>
    """

    return {
        "email_body": html_body,
        "email_subject": f"Processing Report - {results.get('success', 0)} successful, {results.get('failed', 0)} failed"
    }

dynamic_email = send_email(
    to="operations@company.com",
    subject="{{ctx.email_subject}}",
    body="{{ctx.email_body}}",
    html=True,
    name="dynamic_report_email"
)

generate_email_content >> dynamic_email
```

### Conditional Notifications

Send notifications based on workflow conditions:

```python
from microflow import if_node, send_email, slack_notification, task

@task(name="analyze_results")
def analyze_results(ctx):
    error_count = ctx.get("error_count", 0)
    return {
        "has_errors": error_count > 0,
        "is_critical": error_count > 10
    }

# Error notification email
error_email = send_email(
    to="support@company.com",
    subject="Workflow Errors Detected",
    body="The workflow completed with {{ctx.error_count}} errors. Please investigate.",
    name="error_notification"
)

# Critical alert to Slack
critical_slack = slack_notification(
    webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
    message=":warning: CRITICAL: Workflow failed with {{ctx.error_count}} errors!",
    channel="#alerts",
    name="critical_alert"
)

# Conditional notifications
error_notification = if_node(
    condition_expression="ctx.get('has_errors', False)",
    if_true_task=error_email,
    name="send_if_errors"
)

critical_notification = if_node(
    condition_expression="ctx.get('is_critical', False)",
    if_true_task=critical_slack,
    name="send_if_critical"
)

analyze_results >> error_notification >> critical_notification
```

### Multi-Channel Notifications

Send the same notification through multiple channels:

```python
from microflow import task, send_email, slack_notification

@task(name="prepare_notification")
def prepare_notification(ctx):
    return {
        "alert_message": "System maintenance completed successfully.",
        "maintenance_duration": "45 minutes",
        "systems_affected": ["API", "Database", "Web Interface"]
    }

# Email notification
maintenance_email = send_email(
    to=["ops@company.com", "dev@company.com"],
    subject="Maintenance Complete",
    body="""
    Maintenance completed successfully.

    Duration: {{ctx.maintenance_duration}}
    Systems: {{ctx.systems_affected}}

    All systems are now operational.
    """,
    name="maintenance_email"
)

# Slack notification
maintenance_slack = slack_notification(
    webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
    message=":white_check_mark: {{ctx.alert_message}}",
    channel="#operations",
    name="maintenance_slack"
)

# Send to both channels
prepare_notification >> maintenance_email
prepare_notification >> maintenance_slack
```

### Notification with Attachments

Send emails with generated reports or logs:

```python
from microflow import task, write_file, send_email

@task(name="generate_report_file")
def generate_report_file(ctx):
    report_data = ctx.get("daily_stats", {})

    # Generate CSV report
    csv_content = "Date,Processed,Errors,Duration\n"
    csv_content += f"{report_data.get('date')},{report_data.get('processed')},{report_data.get('errors')},{report_data.get('duration')}\n"

    return {"report_csv": csv_content}

save_report = write_file(
    content_key="report_csv",
    file_path="/tmp/daily_report.csv",
    name="save_report_file"
)

email_with_attachment = send_email(
    to="management@company.com",
    subject="Daily Report - {{ctx.daily_stats.date}}",
    body="Please find attached the daily processing report.",
    attachments=["/tmp/daily_report.csv"],
    name="daily_report_email"
)

generate_report_file >> save_report >> email_with_attachment
```

## Slack Block Kit Integration

Use Slack's Block Kit for rich, interactive messages:

```python
from microflow import slack_notification, task

@task(name="prepare_rich_slack_data")
def prepare_rich_slack_data(ctx):
    return {
        "build_status": "success",
        "build_number": 1234,
        "commit_hash": "abc123",
        "test_results": {"passed": 95, "failed": 2}
    }

rich_slack_blocks = slack_notification(
    webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL",
    message="Build Status Update",
    blocks=[
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "Build #{{ctx.build_number}} Complete"
            }
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": "*Status:*\n{{ctx.build_status}}"
                },
                {
                    "type": "mrkdwn",
                    "text": "*Commit:*\n{{ctx.commit_hash}}"
                }
            ]
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": "*Test Results:* {{ctx.test_results.passed}} passed, {{ctx.test_results.failed}} failed"
            }
        },
        {
            "type": "actions",
            "elements": [
                {
                    "type": "button",
                    "text": {
                        "type": "plain_text",
                        "text": "View Build"
                    },
                    "url": "https://ci.company.com/build/{{ctx.build_number}}"
                }
            ]
        }
    ],
    name="build_status_blocks"
)

prepare_rich_slack_data >> rich_slack_blocks
```

## Error Handling and Retry

Handle notification failures gracefully:

```python
from microflow import retry_with_backoff, send_email, slack_notification, task

# Create notification tasks
primary_email = send_email(
    to="primary@company.com",
    subject="Workflow Alert",
    body="Primary notification message",
    name="primary_notification"
)

backup_slack = slack_notification(
    webhook_url="https://hooks.slack.com/services/BACKUP/WEBHOOK/URL",
    message="Backup notification: Primary email failed",
    name="backup_notification"
)

# Add retry logic to primary notification
reliable_email = retry_with_backoff(
    wrapped_task=primary_email,
    max_retries=3,
    initial_delay=5.0,
    name="reliable_email_notification"
)

@task(name="check_notification_success")
def check_notification_success(ctx):
    email_success = ctx.get("email_success", False)
    return {"need_backup": not email_success}

# Fallback to Slack if email fails
backup_notification = if_node(
    condition_expression="ctx.get('need_backup', False)",
    if_true_task=backup_slack,
    name="fallback_notification"
)

reliable_email >> check_notification_success >> backup_notification
```

## Security Considerations

### Credential Management
```python
import os
from microflow import send_email

# Use environment variables for credentials
secure_email = send_email(
    to="recipient@company.com",
    subject="Secure Notification",
    body="This email uses secure credential handling",
    smtp_username=os.getenv("SMTP_USERNAME"),
    smtp_password=os.getenv("SMTP_PASSWORD"),
    smtp_server=os.getenv("SMTP_SERVER", "smtp.company.com"),
    name="secure_email"
)
```

### Content Sanitization
```python
from microflow import task, send_email
import html

@task(name="sanitize_content")
def sanitize_content(ctx):
    user_input = ctx.get("user_message", "")
    # Escape HTML to prevent injection
    safe_content = html.escape(user_input)
    return {"safe_message": safe_content}

safe_email = send_email(
    to="admin@company.com",
    subject="User Feedback",
    body="User message: {{ctx.safe_message}}",
    name="safe_user_email"
)

sanitize_content >> safe_email
```

## Common Patterns

### Status Dashboard Updates
```python
from microflow import slack_notification, task

@task(name="collect_system_status")
def collect_system_status(ctx):
    return {
        "api_status": "healthy",
        "db_status": "healthy",
        "cache_status": "warning",
        "queue_status": "healthy"
    }

status_dashboard = slack_notification(
    webhook_url="https://hooks.slack.com/services/STATUS/WEBHOOK/URL",
    message="System Status Update",
    attachments=[
        {
            "color": "good",
            "title": "System Health Check",
            "fields": [
                {"title": "API", "value": "{{ctx.api_status}}", "short": True},
                {"title": "Database", "value": "{{ctx.db_status}}", "short": True},
                {"title": "Cache", "value": "{{ctx.cache_status}}", "short": True},
                {"title": "Queue", "value": "{{ctx.queue_status}}", "short": True}
            ]
        }
    ],
    name="system_status_update"
)

collect_system_status >> status_dashboard
```

### Escalation Notifications
```python
from microflow import task, send_email, delay

@task(name="check_acknowledgment")
def check_acknowledgment(ctx):
    # Check if alert was acknowledged
    return {"acknowledged": False}  # Simulate unacknowledged

# Initial alert
initial_alert = send_email(
    to="oncall@company.com",
    subject="ALERT: System Issue Detected",
    body="Please acknowledge this alert within 15 minutes.",
    name="initial_alert"
)

# Wait 15 minutes
escalation_delay = delay(900)  # 15 minutes

# Escalation alert
escalation_alert = send_email(
    to="manager@company.com",
    subject="ESCALATION: Unacknowledged Alert",
    body="Previous alert was not acknowledged. Escalating to management.",
    name="escalation_alert"
)

# Conditional escalation
escalation_check = if_node(
    condition_expression="not ctx.get('acknowledged', True)",
    if_true_task=escalation_alert,
    name="escalate_if_unacknowledged"
)

initial_alert >> escalation_delay >> check_acknowledgment >> escalation_check
```

## Best Practices

1. **Use templates**: Create reusable email/message templates
2. **Handle failures**: Always implement retry logic for critical notifications
3. **Secure credentials**: Use environment variables or secure credential stores
4. **Rate limiting**: Respect email/Slack rate limits to avoid blocking
5. **Content validation**: Sanitize user input in notification content
6. **Multiple channels**: Use multiple notification channels for critical alerts
7. **Rich formatting**: Use HTML emails and Slack blocks for better readability
8. **Error context**: Include relevant context and error details in notifications
9. **Test notifications**: Verify notification delivery in different environments
10. **Monitor delivery**: Track notification success rates and delivery times