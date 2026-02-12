# Notification Nodes

Use these nodes to send outbound alerts through channels like email, Slack, and webhook-based systems. Best practices: isolate notification failures from core business flow and tune retries/backoff for each delivery channel.

## API

```python
send_email(
    to_addresses,
    subject,
    body,
    from_address=None,
    smtp_server='localhost',
    smtp_port=587,
    username=None,
    password=None,
    use_tls=True,
    cc_addresses=None,
    bcc_addresses=None,
    attachments=None,
    html_body=None,
    name=None,
    max_retries=2,
    backoff_s=1.0,
)

slack_notification(webhook_url, text, channel=None, username=None, icon_emoji=None, attachments=None, name=None, **kwargs)
discord_notification(webhook_url, content, username=None, avatar_url=None, embeds=None, name=None, **kwargs)
teams_notification(webhook_url, title, text, theme_color='0076D7', sections=None, name=None, **kwargs)
sms_notification(phone_number, message, api_key, service='twilio', from_number=None, name=None, **kwargs)
push_notification(title, body, tokens, service='fcm', api_key='', data=None, name=None, **kwargs)
simple_email(to, subject, body, **kwargs)
alert_email(to, alert_message, severity='INFO', **kwargs)
success_notification(webhook_url, message='Workflow completed successfully')
error_notification(webhook_url, error_message='Workflow failed')
```

## Notes

- Top-level exports in `microflow` include `send_email`, `slack_notification`, and `simple_email`.
- Channel-specific nodes return `*_success` and `*_error` style keys.

## Example

```python
from microflow import send_email, slack_notification

mail = send_email(
    to_addresses="ops@example.com",
    subject="Workflow complete",
    body="Done",
)

slack = slack_notification(
    webhook_url="https://hooks.slack.com/services/...",
    text="Workflow complete",
)
```
