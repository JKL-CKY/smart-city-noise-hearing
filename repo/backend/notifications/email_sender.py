import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncio
import aiosmtplib

from config import settings


class EmailNotificationService:
    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.username = settings.SMTP_USERNAME
        self.password = settings.SMTP_PASSWORD
        self.env_dept_email = settings.ENVIRONMENT_DEPARTMENT_EMAIL
        self.planning_email = settings.URBAN_PLANNING_EMAIL

    async def send_hearing_report(
        self,
        report_id: int,
        hearing_title: str,
        markdown_content: str,
        priority_level: str = "medium",
        attachments: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, bool]:
        """
        Send hearing report to environment department and urban planning commission.
        """
        results = {}

        subject = f"【噪声听证会报告】{hearing_title}"
        if priority_level == "critical":
            subject = f"🔴 紧急 - {subject}"
        elif priority_level == "high":
            subject = f"🟠 高优先级 - {subject}"

        html_content = self._markdown_to_html(markdown_content)

        results['env_dept'] = await self._send_email(
            to_email=self.env_dept_email,
            subject=subject,
            markdown_content=markdown_content,
            html_content=html_content,
            attachments=attachments
        )

        results['planning'] = await self._send_email(
            to_email=self.planning_email,
            subject=subject,
            markdown_content=markdown_content,
            html_content=html_content,
            attachments=attachments
        )

        return results

    async def _send_email(
        self,
        to_email: str,
        subject: str,
        markdown_content: str,
        html_content: str,
        attachments: Optional[List[Dict[str, str]]] = None
    ) -> bool:
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.username
            message["To"] = to_email

            text_part = MIMEText(markdown_content, "plain", "utf-8")
            html_part = MIMEText(html_content, "html", "utf-8")

            message.attach(text_part)
            message.attach(html_part)

            if attachments:
                for att in attachments:
                    if os.path.exists(att['path']):
                        part = MIMEBase("application", "octet-stream")
                        with open(att['path'], "rb") as f:
                            part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            "Content-Disposition",
                            f"attachment; filename= {att['filename']}",
                        )
                        message.attach(part)

            context = ssl.create_default_context()

            if self.smtp_port == 465:
                async with aiosmtplib.SMTP_SSL(
                    hostname=self.smtp_host,
                    port=self.smtp_port,
                    username=self.username,
                    password=self.password,
                    use_tls=True
                ) as server:
                    await server.sendmail(
                        self.username,
                        to_email,
                        message.as_string()
                    )
            else:
                async with aiosmtplib.SMTP(
                    hostname=self.smtp_host,
                    port=self.smtp_port
                ) as server:
                    await server.starttls(context=context)
                    await server.login(self.username, self.password)
                    await server.sendmail(
                        self.username,
                        to_email,
                        message.as_string()
                    )

            return True
        except Exception as e:
            print(f"Failed to send email to {to_email}: {e}")
            return False

    def _markdown_to_html(self, markdown_content: str) -> str:
        import markdown as md
        html = md.markdown(markdown_content, extensions=['tables', 'fenced_code'])

        styled_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>噪声听证会报告</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                h1, h2, h3 {{
                    color: #2c3e50;
                    border-bottom: 2px solid #3498db;
                    padding-bottom: 8px;
                }}
                h1 {{
                    font-size: 24px;
                }}
                h2 {{
                    font-size: 20px;
                    margin-top: 24px;
                }}
                h3 {{
                    font-size: 18px;
                    border-bottom: 1px solid #bdc3c7;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 16px 0;
                }}
                th, td {{
                    border: 1px solid #ddd;
                    padding: 12px;
                    text-align: left;
                }}
                th {{
                    background-color: #3498db;
                    color: white;
                }}
                tr:nth-child(even) {{
                    background-color: #f8f9fa;
                }}
                ul, ol {{
                    padding-left: 24px;
                }}
                li {{
                    margin: 8px 0;
                }}
                hr {{
                    border: 0;
                    border-top: 1px solid #eee;
                    margin: 24px 0;
                }}
                .priority-critical {{
                    color: #e74c3c;
                    font-weight: bold;
                }}
                .priority-high {{
                    color: #e67e22;
                    font-weight: bold;
                }}
                .priority-medium {{
                    color: #f1c40f;
                }}
                .priority-low {{
                    color: #27ae60;
                }}
                .speaker-complainant {{
                    color: #e74c3c;
                }}
                .speaker-official {{
                    color: #3498db;
                }}
            </style>
        </head>
        <body>
            {html}
        </body>
        </html>
        """

        return styled_html

    async def send_notification(
        self,
        to_email: str,
        subject: str,
        message: str
    ) -> bool:
        """Send a simple notification email."""
        try:
            message_obj = MIMEMultipart("alternative")
            message_obj["Subject"] = subject
            message_obj["From"] = self.username
            message_obj["To"] = to_email

            html = f"""
            <html>
                <body>
                    <p>{message}</p>
                    <hr>
                    <p><em>此邮件由智慧城市噪声听证会系统自动发送</em></p>
                </body>
            </html>
            """

            text_part = MIMEText(message, "plain", "utf-8")
            html_part = MIMEText(html, "html", "utf-8")

            message_obj.attach(text_part)
            message_obj.attach(html_part)

            context = ssl.create_default_context()

            if self.smtp_port == 465:
                async with aiosmtplib.SMTP_SSL(
                    hostname=self.smtp_host,
                    port=self.smtp_port,
                    username=self.username,
                    password=self.password,
                    use_tls=True
                ) as server:
                    await server.sendmail(self.username, to_email, message_obj.as_string())
            else:
                async with aiosmtplib.SMTP(hostname=self.smtp_host, port=self.smtp_port) as server:
                    await server.starttls(context=context)
                    await server.login(self.username, self.password)
                    await server.sendmail(self.username, to_email, message_obj.as_string())

            return True
        except Exception as e:
            print(f"Failed to send notification: {e}")
            return False
