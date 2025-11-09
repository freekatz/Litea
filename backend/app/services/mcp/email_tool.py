"""Email notification MCP tool."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any
from .base import MCPTool, MCPToolParameter, MCPToolResult
from app.config import get_settings


class EmailTool(MCPTool):
    """MCP tool for sending email notifications."""
    
    @property
    def name(self) -> str:
        return "send_email"
    
    @property
    def description(self) -> str:
        return "Send email notification with literature updates"
    
    @property
    def parameters(self) -> List[MCPToolParameter]:
        return [
            MCPToolParameter(
                name="to_email",
                type="string",
                description="Recipient email address",
                required=True
            ),
            MCPToolParameter(
                name="subject",
                type="string",
                description="Email subject",
                required=True
            ),
            MCPToolParameter(
                name="body",
                type="string",
                description="Email body (HTML supported)",
                required=True
            ),
            MCPToolParameter(
                name="task_name",
                type="string",
                description="Task name for the email",
                required=False
            ),
        ]
    
    async def execute(self, **kwargs) -> MCPToolResult:
        """
        Send email notification.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body (HTML)
            task_name: Optional task name
            
        Returns:
            MCPToolResult with send status
        """
        try:
            settings = get_settings()
            
            # Check if email is configured
            if not settings.email or not settings.email.smtp_host:
                return MCPToolResult(
                    success=False,
                    error="Email service not configured"
                )
            
            to_email = kwargs["to_email"]
            subject = kwargs["subject"]
            body = kwargs["body"]
            task_name = kwargs.get("task_name", "")
            
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = settings.email.sender
            msg["To"] = to_email
            
            # Attach HTML body
            html_part = MIMEText(body, "html")
            msg.attach(html_part)
            
            # Send email
            self.logger.info(f"Sending email to {to_email}")
            
            # Use SMTP_SSL for port 465, regular SMTP for other ports
            if settings.email.smtp_port == 465:
                # Use SSL connection
                with smtplib.SMTP_SSL(
                    settings.email.smtp_host,
                    settings.email.smtp_port
                ) as server:
                    if settings.email.username and settings.email.password:
                        server.login(
                            settings.email.username,
                            settings.email.password
                        )
                    server.send_message(msg)
            else:
                # Use STARTTLS
                with smtplib.SMTP(
                    settings.email.smtp_host,
                    settings.email.smtp_port
                ) as server:
                    if settings.email.use_tls:
                        server.starttls()
                    
                    if settings.email.username and settings.email.password:
                        server.login(
                            settings.email.username,
                            settings.email.password
                        )
                    server.send_message(msg)
            
            self.logger.info(f"Email sent successfully to {to_email}")
            
            return MCPToolResult(
                success=True,
                data={
                    "to": to_email,
                    "subject": subject,
                    "task_name": task_name
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to send email: {str(e)}")
            return MCPToolResult(
                success=False,
                error=f"Failed to send email: {str(e)}"
            )
    
    def format_documents_html(
        self,
        documents: List[Dict[str, Any]],
        task_name: str
    ) -> str:
        """
        Format documents list into HTML email body.
        
        Args:
            documents: List of document data
            task_name: Task name
            
        Returns:
            HTML string
        """
        html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                }}
                .header {{
                    background: linear-gradient(135deg, #f59e0b 0%, #ea580c 100%);
                    color: white;
                    padding: 20px;
                    border-radius: 8px 8px 0 0;
                }}
                .content {{
                    padding: 20px;
                    background: #f9fafb;
                }}
                .document {{
                    background: white;
                    padding: 15px;
                    margin-bottom: 15px;
                    border-radius: 8px;
                    border-left: 4px solid #f59e0b;
                }}
                .doc-title {{
                    font-size: 18px;
                    font-weight: bold;
                    color: #1f2937;
                    margin-bottom: 8px;
                }}
                .doc-meta {{
                    color: #6b7280;
                    font-size: 14px;
                    margin-bottom: 8px;
                }}
                .doc-summary {{
                    background: #fef3c7;
                    padding: 10px;
                    border-radius: 4px;
                    margin: 10px 0;
                    border-left: 3px solid #f59e0b;
                }}
                .doc-abstract {{
                    color: #4b5563;
                    font-size: 14px;
                    line-height: 1.5;
                }}
                .keywords {{
                    margin-top: 10px;
                }}
                .keyword {{
                    display: inline-block;
                    background: #dbeafe;
                    color: #1e40af;
                    padding: 3px 8px;
                    border-radius: 4px;
                    font-size: 12px;
                    margin-right: 5px;
                    margin-top: 5px;
                }}
                .footer {{
                    text-align: center;
                    color: #9ca3af;
                    font-size: 12px;
                    padding: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>☕ Litea 文献推送</h1>
                <p>任务: {task_name}</p>
            </div>
            <div class="content">
                <p>共找到 <strong>{len(documents)}</strong> 篇相关文献:</p>
        """
        
        for doc in documents:
            html += f"""
                <div class="document">
                    <div class="doc-title">{doc.get('title', 'Untitled')}</div>
                    <div class="doc-meta">
                        <span>来源: {doc.get('source', 'Unknown')}</span>
                        {f" | 评分: {doc.get('score', 0):.2f}" if doc.get('score') is not None else ""}
                        {f" | 发布: {str(doc.get('published_at', ''))[:10]}" if doc.get('published_at') else ""}
                        {f" | 作者: {', '.join(doc.get('authors', [])[:3])}" if doc.get('authors') else ""}
                    </div>
            """
            
            if doc.get('summary'):
                html += f"""
                    <div class="doc-summary">
                        <strong>🤖 AI 总结:</strong> {doc['summary']}
                    </div>
                """
            
            if doc.get('highlights'):
                html += '<div class="doc-summary" style="background: #e0f2fe; border-left-color: #0284c7;">'
                html += '<strong>💡 关键亮点:</strong><ul style="margin: 5px 0; padding-left: 20px;">'
                for highlight in doc['highlights'][:5]:
                    html += f'<li>{highlight}</li>'
                html += '</ul></div>'
            
            if doc.get('abstract'):
                html += f"""
                    <div class="doc-abstract">
                        <strong>摘要:</strong> {doc['abstract'][:400]}{'...' if len(doc.get('abstract', '')) > 400 else ''}
                    </div>
                """
            
            if doc.get('keywords'):
                html += '<div class="keywords">'
                for kw in doc['keywords'][:10]:
                    html += f'<span class="keyword">{kw}</span>'
                html += '</div>'
            
            if doc.get('url'):
                html += f'<p><a href="{doc["url"]}" style="color: #f59e0b;">📄 查看原文</a></p>'
            
            html += "</div>"
        
        html += """
            </div>
            <div class="footer">
                <p>此邮件由 Litea 自动发送 - Literature with a cup of tea!</p>
            </div>
        </body>
        </html>
        """
        
        return html
