"""Feishu (Lark) webhook notification MCP tool."""

import aiohttp
from typing import List, Dict, Any
from .base import MCPTool, MCPToolParameter, MCPToolResult


class FeishuTool(MCPTool):
    """MCP tool for sending notifications to Feishu group webhook."""
    
    @property
    def name(self) -> str:
        return "send_feishu"
    
    @property
    def description(self) -> str:
        return "Send notification to Feishu (Lark) group via webhook"
    
    @property
    def parameters(self) -> List[MCPToolParameter]:
        return [
            MCPToolParameter(
                name="webhook_url",
                type="string",
                description="Feishu webhook URL",
                required=True
            ),
            MCPToolParameter(
                name="task_name",
                type="string",
                description="Task name",
                required=True
            ),
            MCPToolParameter(
                name="documents_count",
                type="integer",
                description="Number of documents",
                required=True
            ),
            MCPToolParameter(
                name="documents",
                type="array",
                description="List of documents",
                required=False
            ),
        ]
    
    async def execute(self, **kwargs) -> MCPToolResult:
        """
        Send notification to Feishu webhook.
        
        Args:
            webhook_url: Feishu webhook URL
            task_name: Task name
            documents_count: Number of documents
            documents: List of documents (optional)
            
        Returns:
            MCPToolResult with send status
        """
        try:
            webhook_url = kwargs["webhook_url"]
            task_name = kwargs["task_name"]
            documents_count = kwargs["documents_count"]
            documents = kwargs.get("documents", [])
            
            # Build message card
            message = self.build_message_card(
                task_name,
                documents_count,
                documents
            )
            
            # Send to webhook
            self.logger.info(f"Sending to Feishu webhook: {task_name}")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=message,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    response_text = await response.text()
                    
                    if response.status != 200:
                        raise Exception(
                            f"Feishu webhook returned {response.status}: "
                            f"{response_text}"
                        )
                    
                    self.logger.info(
                        f"Feishu notification sent successfully: {task_name}"
                    )
                    
                    return MCPToolResult(
                        success=True,
                        data={
                            "task_name": task_name,
                            "documents_count": documents_count,
                            "webhook_url": webhook_url[:50] + "..."
                        }
                    )
        
        except Exception as e:
            self.logger.error(f"Failed to send Feishu notification: {str(e)}")
            return MCPToolResult(
                success=False,
                error=f"Failed to send Feishu notification: {str(e)}"
            )
    
    def build_message_card(
        self,
        task_name: str,
        documents_count: int,
        documents: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Build Feishu message card.
        
        Args:
            task_name: Task name
            documents_count: Number of documents
            documents: List of documents
            
        Returns:
            Message card dict
        """
        # Build elements
        elements = [
            {
                "tag": "markdown",
                "content": f"**任务名称:** {task_name}\n"
                          f"**文献数量:** {documents_count} 篇"
            }
        ]
        
        # Add top documents (max 5)
        if documents:
            elements.append({
                "tag": "hr"
            })
            elements.append({
                "tag": "markdown",
                "content": "**📚 最新文献:**"
            })
            
            for i, doc in enumerate(documents[:5], 1):
                title = doc.get('title', 'Untitled')
                source = doc.get('source', 'Unknown')
                score = doc.get('score')
                url = doc.get('url', '')
                
                content = f"**{i}. {title}**\n"
                content += f"来源: {source}"
                
                if score is not None:
                    content += f" | 评分: {score:.2f}"
                
                # Add summary if available
                if doc.get('summary'):
                    content += f"\n🤖 {doc['summary'][:150]}..."
                
                # Add highlights if available
                if doc.get('highlights'):
                    highlights_text = " | ".join(doc['highlights'][:2])
                    content += f"\n💡 {highlights_text}"
                
                # Add URL if available
                if url:
                    content += f"\n[📄 查看原文]({url})"
                
                elements.append({
                    "tag": "markdown",
                    "content": content
                })
            
            if len(documents) > 5:
                elements.append({
                    "tag": "note",
                    "elements": [{
                        "tag": "plain_text",
                        "content": f"还有 {len(documents) - 5} 篇文献，"
                                  f"请查看邮件或系统获取完整列表"
                    }]
                })
        
        # Build card
        message = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": "☕ Litea 文献推送"
                    },
                    "template": "orange"
                },
                "elements": elements
            }
        }
        
        return message
