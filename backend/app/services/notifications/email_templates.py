"""Email template rendering with Jinja2."""

from __future__ import annotations

from typing import Any, Dict, List

from jinja2 import Template

# 分组显示模式模板
EMAIL_TEMPLATE_GROUPED = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', sans-serif;
    line-height: 1.6;
    color: #333;
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
    background-color: #f5f5f5;
  }
  .container {
    background-color: white;
    border-radius: 8px;
    padding: 30px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  }
  h1 {
    color: #2c3e50;
    border-bottom: 3px solid #3498db;
    padding-bottom: 10px;
    margin-bottom: 20px;
  }
  .summary {
    background-color: #f8f9fa;
    padding: 15px;
    border-left: 4px solid #3498db;
    margin: 20px 0;
    border-radius: 4px;
  }
  .source-section {
    margin: 30px 0;
  }
  .source-header {
    background-color: #3498db;
    color: white;
    padding: 10px 15px;
    border-radius: 4px;
    font-size: 18px;
    font-weight: bold;
  }
  .paper {
    background-color: #fff;
    border: 1px solid #e0e0e0;
    border-left: 4px solid #3498db;
    padding: 15px;
    margin: 15px 0;
    border-radius: 4px;
    transition: box-shadow 0.3s;
  }
  .paper:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
  }
  .paper-title {
    font-size: 16px;
    font-weight: bold;
    color: #2c3e50;
    margin-bottom: 8px;
  }
  .paper-meta {
    font-size: 14px;
    color: #7f8c8d;
    margin-bottom: 8px;
  }
  .paper-score {
    display: inline-block;
    background-color: #27ae60;
    color: white;
    padding: 2px 8px;
    border-radius: 12px;
    font-size: 12px;
    font-weight: bold;
  }
  .paper-summary {
    color: #555;
    font-size: 14px;
    margin: 10px 0;
  }
  .paper-link {
    color: #3498db;
    text-decoration: none;
    font-weight: 500;
  }
  .paper-link:hover {
    text-decoration: underline;
  }
  .more-link {
    text-align: center;
    margin-top: 20px;
  }
  .more-link a {
    display: inline-block;
    background-color: #3498db;
    color: white;
    padding: 10px 20px;
    border-radius: 4px;
    text-decoration: none;
    font-weight: 500;
  }
  .footer {
    text-align: center;
    margin-top: 30px;
    padding-top: 20px;
    border-top: 1px solid #e0e0e0;
    color: #7f8c8d;
    font-size: 14px;
  }
</style>
</head>
<body>
  <div class="container">
    <h1>📚 {{ task_name }} - 文献推送</h1>
    
    {% if trend_summary %}
    <div class="summary">
      <strong>📊 趋势总结</strong>
      <p>{{ trend_summary }}</p>
    </div>
    {% endif %}
    
    {% for source_name, docs in grouped_docs.items() %}
    <div class="source-section">
      <div class="source-header">
        📖 来源：{{ source_name }} ({{ docs|length }} 篇)
      </div>
      
      {% for doc in docs[:per_source_limit] %}
      <div class="paper">
        <div class="paper-title">{{ doc.title }}</div>
        <div class="paper-meta">
          <span class="paper-score">⭐ {{ "%.2f"|format(doc.score or 0) }}</span>
          {% if doc.authors %}
          <span> | 作者: {{ doc.authors[:3]|join(', ') }}{% if doc.authors|length > 3 %} 等{% endif %}</span>
          {% endif %}
        </div>
        {% if doc.summary %}
        <div class="paper-summary">{{ doc.summary }}</div>
        {% endif %}
        <div>
          <a href="{{ doc.url }}" class="paper-link" target="_blank">🔗 查看原文</a>
        </div>
      </div>
      {% endfor %}
      
      {% if docs|length > per_source_limit %}
      <div class="more-link">
        <a href="{{ web_url }}/documents?task_id={{ task_id }}&source={{ source_name }}">
          查看全部 {{ docs|length }} 篇文献 →
        </a>
      </div>
      {% endif %}
    </div>
    {% endfor %}
    
    <div class="footer">
      <p>本邮件由 Litea 文献助手自动生成</p>
      <p><a href="{{ web_url }}" style="color: #3498db;">访问 Litea 查看更多</a></p>
    </div>
  </div>
</body>
</html>
"""

# 排名显示模式模板
EMAIL_TEMPLATE_RANKED = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<style>
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', sans-serif;
    line-height: 1.6;
    color: #333;
    max-width: 800px;
    margin: 0 auto;
    padding: 20px;
    background-color: #f5f5f5;
  }
  .container {
    background-color: white;
    border-radius: 8px;
    padding: 30px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  }
  h1 {
    color: #2c3e50;
    border-bottom: 3px solid #e74c3c;
    padding-bottom: 10px;
    margin-bottom: 20px;
  }
  .summary {
    background-color: #f8f9fa;
    padding: 15px;
    border-left: 4px solid #e74c3c;
    margin: 20px 0;
    border-radius: 4px;
  }
  .rankings {
    margin: 30px 0;
  }
  .rank-item {
    display: flex;
    align-items: start;
    background-color: #fff;
    border: 1px solid #e0e0e0;
    padding: 20px;
    margin: 15px 0;
    border-radius: 4px;
    transition: all 0.3s;
  }
  .rank-item:hover {
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    transform: translateY(-2px);
  }
  .rank-number {
    font-size: 32px;
    font-weight: bold;
    color: #e74c3c;
    min-width: 60px;
    text-align: center;
  }
  .rank-content {
    flex: 1;
    padding-left: 20px;
  }
  .paper-title {
    font-size: 18px;
    font-weight: bold;
    color: #2c3e50;
    margin-bottom: 10px;
  }
  .paper-meta {
    font-size: 14px;
    color: #7f8c8d;
    margin-bottom: 10px;
  }
  .paper-score {
    display: inline-block;
    background-color: #e74c3c;
    color: white;
    padding: 3px 10px;
    border-radius: 12px;
    font-size: 13px;
    font-weight: bold;
  }
  .paper-summary {
    color: #555;
    font-size: 14px;
    margin: 10px 0;
    line-height: 1.5;
  }
  .paper-reason {
    background-color: #fff3cd;
    border-left: 3px solid #ffc107;
    padding: 10px;
    margin: 10px 0;
    font-size: 13px;
    border-radius: 4px;
  }
  .paper-link {
    color: #e74c3c;
    text-decoration: none;
    font-weight: 500;
  }
  .paper-link:hover {
    text-decoration: underline;
  }
  .footer {
    text-align: center;
    margin-top: 30px;
    padding-top: 20px;
    border-top: 1px solid #e0e0e0;
    color: #7f8c8d;
    font-size: 14px;
  }
</style>
</head>
<body>
  <div class="container">
    <h1>🏆 {{ task_name }} - Top {{ rankings|length }} 文献推荐</h1>
    
    {% if trend_summary %}
    <div class="summary">
      <strong>📊 趋势总结</strong>
      <p>{{ trend_summary }}</p>
    </div>
    {% endif %}
    
    <div class="rankings">
      {% for item in rankings %}
      <div class="rank-item">
        <div class="rank-number">#{{ loop.index }}</div>
        <div class="rank-content">
          <div class="paper-title">{{ item.title }}</div>
          <div class="paper-meta">
            <span class="paper-score">⭐ {{ "%.2f"|format(item.score) }}</span>
            {% if item.authors %}
            <span> | {{ item.authors[:3]|join(', ') }}{% if item.authors|length > 3 %} 等{% endif %}</span>
            {% endif %}
            <span> | {{ item.source }}</span>
          </div>
          {% if item.summary %}
          <div class="paper-summary">{{ item.summary }}</div>
          {% endif %}
          {% if item.reason %}
          <div class="paper-reason">
            <strong>💡 推荐理由：</strong> {{ item.reason }}
          </div>
          {% endif %}
          <div>
            <a href="{{ item.url }}" class="paper-link" target="_blank">🔗 查看原文</a>
          </div>
        </div>
      </div>
      {% endfor %}
    </div>
    
    <div class="footer">
      <p>本邮件由 Litea 文献助手自动生成</p>
      <p><a href="{{ web_url }}/documents?task_id={{ task_id }}" style="color: #e74c3c;">查看全部文献 →</a></p>
    </div>
  </div>
</body>
</html>
"""


class EmailTemplateRenderer:
    """Render email templates with different display modes."""

    def __init__(self) -> None:
        self.template_grouped = Template(EMAIL_TEMPLATE_GROUPED)
        self.template_ranked = Template(EMAIL_TEMPLATE_RANKED)

    def render_grouped(
        self,
        task_name: str,
        task_id: int,
        grouped_docs: Dict[str, List[Dict[str, Any]]],
        trend_summary: str = "",
        per_source_limit: int = 5,
        web_url: str = "http://localhost:3000",
    ) -> str:
        """Render email in grouped-by-source mode."""
        return self.template_grouped.render(
            task_name=task_name,
            task_id=task_id,
            grouped_docs=grouped_docs,
            trend_summary=trend_summary,
            per_source_limit=per_source_limit,
            web_url=web_url,
        )

    def render_ranked(
        self,
        task_name: str,
        task_id: int,
        rankings: List[Dict[str, Any]],
        trend_summary: str = "",
        web_url: str = "http://localhost:3000",
    ) -> str:
        """Render email in ranked mode (Top N)."""
        return self.template_ranked.render(
            task_name=task_name,
            task_id=task_id,
            rankings=rankings,
            trend_summary=trend_summary,
            web_url=web_url,
        )
