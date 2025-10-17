"""Notification nodes for email, SMS, Slack, etc."""

import asyncio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from ..core.task_spec import task


def send_email(
    to_addresses: Union[str, List[str]],
    subject: str,
    body: str,
    from_address: Optional[str] = None,
    smtp_server: str = "localhost",
    smtp_port: int = 587,
    username: Optional[str] = None,
    password: Optional[str] = None,
    use_tls: bool = True,
    cc_addresses: Optional[Union[str, List[str]]] = None,
    bcc_addresses: Optional[Union[str, List[str]]] = None,
    attachments: Optional[List[str]] = None,
    html_body: Optional[str] = None,
    name: Optional[str] = None,
    max_retries: int = 2,
    backoff_s: float = 1.0
):
    """
    Send email notification.

    Args:
        to_addresses: Recipient email addresses
        subject: Email subject
        body: Email body (plain text)
        from_address: Sender email address
        smtp_server: SMTP server hostname
        smtp_port: SMTP server port
        username: SMTP username
        password: SMTP password
        use_tls: Whether to use TLS encryption
        cc_addresses: CC email addresses
        bcc_addresses: BCC email addresses
        attachments: List of file paths to attach
        html_body: HTML version of email body
        name: Node name
        max_retries: Number of retry attempts
        backoff_s: Backoff time between retries

    Returns email results in context:
        - email_sent: Whether email was sent successfully
        - email_recipients: List of recipients
        - email_subject: Email subject
        - email_message_id: Message ID if available
    """
    node_name = name or "send_email"

    @task(name=node_name, max_retries=max_retries, backoff_s=backoff_s,
          description=f"Send email: {subject}")
    async def _send_email(ctx):
        # Resolve dynamic values from context
        resolved_to = to_addresses
        if isinstance(to_addresses, str):
            resolved_to = to_addresses.format(**ctx)
            resolved_to = [addr.strip() for addr in resolved_to.split(',')]
        elif isinstance(to_addresses, list):
            resolved_to = [addr.format(**ctx) if isinstance(addr, str) else addr for addr in to_addresses]

        resolved_subject = subject.format(**ctx) if isinstance(subject, str) else subject
        resolved_body = body.format(**ctx) if isinstance(body, str) else body
        resolved_from = from_address.format(**ctx) if from_address and isinstance(from_address, str) else from_address

        # Resolve CC and BCC
        resolved_cc = []
        if cc_addresses:
            if isinstance(cc_addresses, str):
                resolved_cc = [addr.strip() for addr in cc_addresses.format(**ctx).split(',')]
            else:
                resolved_cc = cc_addresses

        resolved_bcc = []
        if bcc_addresses:
            if isinstance(bcc_addresses, str):
                resolved_bcc = [addr.strip() for addr in bcc_addresses.format(**ctx).split(',')]
            else:
                resolved_bcc = bcc_addresses

        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = resolved_subject
            msg['From'] = resolved_from or username or "noreply@example.com"
            msg['To'] = ', '.join(resolved_to)

            if resolved_cc:
                msg['Cc'] = ', '.join(resolved_cc)

            # Add body parts
            if resolved_body:
                text_part = MIMEText(resolved_body, 'plain', 'utf-8')
                msg.attach(text_part)

            if html_body:
                resolved_html = html_body.format(**ctx) if isinstance(html_body, str) else html_body
                html_part = MIMEText(resolved_html, 'html', 'utf-8')
                msg.attach(html_part)

            # Add attachments
            if attachments:
                for attachment_path in attachments:
                    resolved_path = attachment_path.format(**ctx) if isinstance(attachment_path, str) else attachment_path
                    path_obj = Path(resolved_path)

                    if path_obj.exists():
                        with open(path_obj, 'rb') as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())

                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {path_obj.name}'
                        )
                        msg.attach(part)

            # Send email
            all_recipients = resolved_to + resolved_cc + resolved_bcc

            # Connect to SMTP server
            server = smtplib.SMTP(smtp_server, smtp_port)

            if use_tls:
                server.starttls()

            if username and password:
                server.login(username, password)

            # Send email
            text = msg.as_string()
            server.sendmail(resolved_from or username, all_recipients, text)
            server.quit()

            return {
                "email_sent": True,
                "email_recipients": all_recipients,
                "email_subject": resolved_subject,
                "email_from": resolved_from or username,
                "email_attachments": len(attachments) if attachments else 0
            }

        except Exception as e:
            return {
                "email_sent": False,
                "email_error": str(e),
                "email_recipients": resolved_to,
                "email_subject": resolved_subject
            }

    return _send_email


def slack_notification(
    webhook_url: str,
    text: str,
    channel: Optional[str] = None,
    username: Optional[str] = None,
    icon_emoji: Optional[str] = None,
    attachments: Optional[List[Dict]] = None,
    name: Optional[str] = None,
    **kwargs
):
    """
    Send Slack notification via webhook.

    Args:
        webhook_url: Slack webhook URL
        text: Message text
        channel: Channel to post to (overrides webhook default)
        username: Bot username
        icon_emoji: Bot icon emoji
        attachments: Slack message attachments
        name: Node name
        **kwargs: Additional arguments for http_request

    Note: Requires http_request functionality
    """
    from .http_request import http_post

    node_name = name or "slack_notification"

    @task(name=node_name, description="Send Slack notification")
    async def _slack_notification(ctx):
        # Build Slack payload
        payload = {
            "text": text.format(**ctx) if isinstance(text, str) else text
        }

        if channel:
            payload["channel"] = channel.format(**ctx) if isinstance(channel, str) else channel

        if username:
            payload["username"] = username.format(**ctx) if isinstance(username, str) else username

        if icon_emoji:
            payload["icon_emoji"] = icon_emoji

        if attachments:
            # Resolve attachments from context
            resolved_attachments = []
            for attachment in attachments:
                if isinstance(attachment, dict):
                    resolved_attachment = {}
                    for key, value in attachment.items():
                        if isinstance(value, str):
                            resolved_attachment[key] = value.format(**ctx)
                        else:
                            resolved_attachment[key] = value
                    resolved_attachments.append(resolved_attachment)
            payload["attachments"] = resolved_attachments

        # Use http_post to send the webhook
        http_task = http_post(
            url=webhook_url,
            json_data=payload,
            name=node_name,
            **kwargs
        )

        result = await http_task.spec.fn(ctx)

        # Transform HTTP result to Slack-specific result
        return {
            "slack_sent": result.get("http_success", False),
            "slack_status_code": result.get("http_status_code"),
            "slack_response": result.get("http_data"),
            "slack_error": None if result.get("http_success") else result.get("http_data"),
            "slack_text": payload["text"]
        }

    return _slack_notification


def discord_notification(
    webhook_url: str,
    content: str,
    username: Optional[str] = None,
    avatar_url: Optional[str] = None,
    embeds: Optional[List[Dict]] = None,
    name: Optional[str] = None,
    **kwargs
):
    """
    Send Discord notification via webhook.

    Args:
        webhook_url: Discord webhook URL
        content: Message content
        username: Bot username
        avatar_url: Bot avatar URL
        embeds: Discord embeds
        name: Node name
        **kwargs: Additional arguments for http_request
    """
    from .http_request import http_post

    node_name = name or "discord_notification"

    @task(name=node_name, description="Send Discord notification")
    async def _discord_notification(ctx):
        # Build Discord payload
        payload = {
            "content": content.format(**ctx) if isinstance(content, str) else content
        }

        if username:
            payload["username"] = username.format(**ctx) if isinstance(username, str) else username

        if avatar_url:
            payload["avatar_url"] = avatar_url.format(**ctx) if isinstance(avatar_url, str) else avatar_url

        if embeds:
            # Resolve embeds from context
            resolved_embeds = []
            for embed in embeds:
                if isinstance(embed, dict):
                    resolved_embed = {}
                    for key, value in embed.items():
                        if isinstance(value, str):
                            resolved_embed[key] = value.format(**ctx)
                        else:
                            resolved_embed[key] = value
                    resolved_embeds.append(resolved_embed)
            payload["embeds"] = resolved_embeds

        # Use http_post to send the webhook
        http_task = http_post(
            url=webhook_url,
            json_data=payload,
            name=node_name,
            **kwargs
        )

        result = await http_task.spec.fn(ctx)

        return {
            "discord_sent": result.get("http_success", False),
            "discord_status_code": result.get("http_status_code"),
            "discord_response": result.get("http_data"),
            "discord_error": None if result.get("http_success") else result.get("http_data"),
            "discord_content": payload["content"]
        }

    return _discord_notification


def teams_notification(
    webhook_url: str,
    title: str,
    text: str,
    theme_color: str = "0076D7",
    sections: Optional[List[Dict]] = None,
    name: Optional[str] = None,
    **kwargs
):
    """
    Send Microsoft Teams notification via webhook.

    Args:
        webhook_url: Teams webhook URL
        title: Message title
        text: Message text
        theme_color: Theme color (hex)
        sections: Teams message sections
        name: Node name
        **kwargs: Additional arguments for http_request
    """
    from .http_request import http_post

    node_name = name or "teams_notification"

    @task(name=node_name, description="Send Teams notification")
    async def _teams_notification(ctx):
        # Build Teams payload
        payload = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": theme_color,
            "summary": title.format(**ctx) if isinstance(title, str) else title,
            "title": title.format(**ctx) if isinstance(title, str) else title,
            "text": text.format(**ctx) if isinstance(text, str) else text
        }

        if sections:
            # Resolve sections from context
            resolved_sections = []
            for section in sections:
                if isinstance(section, dict):
                    resolved_section = {}
                    for key, value in section.items():
                        if isinstance(value, str):
                            resolved_section[key] = value.format(**ctx)
                        else:
                            resolved_section[key] = value
                    resolved_sections.append(resolved_section)
            payload["sections"] = resolved_sections

        # Use http_post to send the webhook
        http_task = http_post(
            url=webhook_url,
            json_data=payload,
            name=node_name,
            **kwargs
        )

        result = await http_task.spec.fn(ctx)

        return {
            "teams_sent": result.get("http_success", False),
            "teams_status_code": result.get("http_status_code"),
            "teams_response": result.get("http_data"),
            "teams_error": None if result.get("http_success") else result.get("http_data"),
            "teams_title": payload["title"]
        }

    return _teams_notification


def sms_notification(
    phone_number: str,
    message: str,
    api_key: str,
    service: str = "twilio",
    from_number: Optional[str] = None,
    name: Optional[str] = None,
    **kwargs
):
    """
    Send SMS notification (requires external SMS service).

    Args:
        phone_number: Recipient phone number
        message: SMS message text
        api_key: SMS service API key
        service: SMS service provider ("twilio", "nexmo", etc.)
        from_number: Sender phone number
        name: Node name
        **kwargs: Additional service-specific parameters
    """
    node_name = name or "sms_notification"

    @task(name=node_name, description=f"Send SMS to {phone_number}")
    async def _sms_notification(ctx):
        resolved_phone = phone_number.format(**ctx) if isinstance(phone_number, str) else phone_number
        resolved_message = message.format(**ctx) if isinstance(message, str) else message

        if service.lower() == "twilio":
            return await _send_twilio_sms(ctx, resolved_phone, resolved_message, api_key, from_number, **kwargs)
        else:
            return {
                "sms_sent": False,
                "sms_error": f"Unsupported SMS service: {service}",
                "sms_phone": resolved_phone
            }

    async def _send_twilio_sms(ctx, phone, msg, api_key, from_num, **kwargs):
        """Send SMS via Twilio API"""
        from .http_request import http_post
        from .http_request import BasicAuth

        # Twilio API endpoint (would need account SID)
        account_sid = kwargs.get("account_sid")
        if not account_sid:
            return {
                "sms_sent": False,
                "sms_error": "Twilio account_sid required",
                "sms_phone": phone
            }

        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"

        # Prepare form data
        form_data = {
            "To": phone,
            "Body": msg
        }

        if from_num:
            form_data["From"] = from_num.format(**ctx) if isinstance(from_num, str) else from_num

        # Send request
        http_task = http_post(
            url=url,
            form_data=form_data,
            auth=BasicAuth(account_sid, api_key),
            name="twilio_sms"
        )

        result = await http_task.spec.fn(ctx)

        return {
            "sms_sent": result.get("http_success", False),
            "sms_status_code": result.get("http_status_code"),
            "sms_response": result.get("http_data"),
            "sms_error": None if result.get("http_success") else result.get("http_data"),
            "sms_phone": phone,
            "sms_message": msg
        }

    return _sms_notification


def push_notification(
    title: str,
    body: str,
    tokens: Union[str, List[str]],
    service: str = "fcm",
    api_key: str = "",
    data: Optional[Dict] = None,
    name: Optional[str] = None,
    **kwargs
):
    """
    Send push notification to mobile devices.

    Args:
        title: Notification title
        body: Notification body
        tokens: Device tokens (string or list)
        service: Push service ("fcm" for Firebase)
        api_key: Service API key
        data: Additional data payload
        name: Node name
        **kwargs: Additional service parameters
    """
    node_name = name or "push_notification"

    @task(name=node_name, description=f"Send push notification: {title}")
    async def _push_notification(ctx):
        resolved_title = title.format(**ctx) if isinstance(title, str) else title
        resolved_body = body.format(**ctx) if isinstance(body, str) else body

        # Resolve tokens
        resolved_tokens = tokens
        if isinstance(tokens, str):
            resolved_tokens = [tokens.format(**ctx)]
        elif isinstance(tokens, list):
            resolved_tokens = [token.format(**ctx) if isinstance(token, str) else token for token in tokens]

        if service.lower() == "fcm":
            return await _send_fcm_notification(ctx, resolved_title, resolved_body, resolved_tokens, api_key, data, **kwargs)
        else:
            return {
                "push_sent": False,
                "push_error": f"Unsupported push service: {service}",
                "push_tokens": resolved_tokens
            }

    async def _send_fcm_notification(ctx, title, body, tokens, api_key, data, **kwargs):
        """Send push notification via Firebase Cloud Messaging"""
        from .http_request import http_post, BearerAuth

        url = "https://fcm.googleapis.com/fcm/send"

        # Build FCM payload
        payload = {
            "notification": {
                "title": title,
                "body": body
            }
        }

        if data:
            resolved_data = {}
            for key, value in data.items():
                if isinstance(value, str):
                    resolved_data[key] = value.format(**ctx)
                else:
                    resolved_data[key] = value
            payload["data"] = resolved_data

        sent_count = 0
        failed_count = 0
        responses = []

        # Send to each token
        for token in tokens:
            payload["to"] = token

            http_task = http_post(
                url=url,
                json_data=payload,
                auth=BearerAuth(api_key),
                name="fcm_push"
            )

            result = await http_task.spec.fn(ctx)
            responses.append(result)

            if result.get("http_success", False):
                sent_count += 1
            else:
                failed_count += 1

        return {
            "push_sent": sent_count > 0,
            "push_sent_count": sent_count,
            "push_failed_count": failed_count,
            "push_total_tokens": len(tokens),
            "push_responses": responses,
            "push_title": title,
            "push_body": body
        }

    return _push_notification


# Convenience functions for common notification patterns
def simple_email(to: str, subject: str, body: str, **kwargs):
    """Simple email notification with minimal configuration"""
    return send_email(
        to_addresses=to,
        subject=subject,
        body=body,
        name="simple_email",
        **kwargs
    )


def alert_email(to: str, alert_message: str, severity: str = "INFO", **kwargs):
    """Alert email with standard formatting"""
    subject = f"[{severity}] Alert: {alert_message}"
    body = f"""
Alert Notification
==================

Severity: {severity}
Message: {alert_message}
Time: {{timestamp}}
Workflow: {{workflow_name}}

This is an automated alert from Microflow.
"""
    return send_email(
        to_addresses=to,
        subject=subject,
        body=body,
        name=f"alert_email_{severity.lower()}",
        **kwargs
    )


def success_notification(webhook_url: str, message: str = "Workflow completed successfully"):
    """Success notification to Slack/Teams"""
    return slack_notification(
        webhook_url=webhook_url,
        text=f"✅ {message}",
        name="success_notification"
    )


def error_notification(webhook_url: str, error_message: str = "Workflow failed"):
    """Error notification to Slack/Teams"""
    return slack_notification(
        webhook_url=webhook_url,
        text=f"❌ {error_message}",
        name="error_notification"
    )