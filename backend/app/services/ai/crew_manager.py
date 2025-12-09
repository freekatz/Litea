"""CrewAI orchestration helpers with LiteLLM support."""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

from crewai import Agent, Crew, Process, Task
from loguru import logger

from ...config import get_settings
from .provider_registry import ProviderRegistry


_SETTINGS = get_settings()
_STATIC_PROMPTS = _SETTINGS.static.prompts if _SETTINGS.static else {}

_FALLBACK_FILTER_PROMPT = """请仔细阅读文献的完整信息，特别是摘要部分，然后评估：

1. **相关性判断** (is_selected):
    - 文献内容是否与研究主题直接相关？
    - 是否包含所需的关键信息或方法？
    - 返回 true（相关）或 false（不相关）

2. **相关性评分** (score):
    - 给出 0-1 之间的相关性评分
    - 0.8-1.0: 高度相关，核心文献
    - 0.6-0.8: 中度相关，参考价值
    - 0.4-0.6: 低度相关，边缘相关
    - 0.0-0.4: 基本不相关

3. **文献总结** (summary):
    - 用1-2句话总结文献的核心内容
    - 说明为什么选择或不选择这篇文献

4. **关键亮点** (highlights):
    - 列出2-4个关键发现或创新点
    - 与研究主题最相关的部分"""

_FALLBACK_SUMMARY_PROMPT = """对筛选后的文献进行深度分析和综合总结。

请从以下角度进行分析，所有输出内容均需使用中文表达：

1. **趋势总结** (trend_summary):
    - 当前研究领域的主要趋势和发展方向
    - 热点问题和研究焦点
    - 技术路线和方法论的演进
    - 2-3个段落，清晰连贯

2. **文献排名** (rankings):
    - 按重要性和相关性对文献进行排序
    - 说明每篇文献的核心贡献和推荐理由
    - 最多10篇

3. **主题分类** (sections):
    - 按研究主题或方法论对文献进行分组
    - 每个类别包含相关文献列表和简要描述
    - 4-6个主题类别

4. **关键洞察** (key_insights):
    - 从文献中提炼的关键发现和创新点
    - 值得关注的研究进展
    - 5-8条核心观点

5. **研究方向建议** (research_directions):
    - 基于当前文献的未来研究方向建议
    - 潜在的研究缺口和机会
    - 3-5个方向"""

DEFAULT_FILTER_PROMPT = _STATIC_PROMPTS.get("filter_default", _FALLBACK_FILTER_PROMPT)
DEFAULT_SUMMARY_PROMPT = _STATIC_PROMPTS.get("summary_default", _FALLBACK_SUMMARY_PROMPT)


class CrewManager:
    """Wrap crew creation for filtering and summarization flows."""

    def __init__(self, provider_registry: ProviderRegistry | None = None) -> None:
        self._registry = provider_registry or ProviderRegistry()
        self._setup_environment()

    def _setup_environment(self) -> None:
        """Setup environment variables for LiteLLM providers."""
        settings = get_settings()
        provider = self._registry.get(settings.ai.default_provider)
        
        # Setup DeepSeek environment variables for LiteLLM
        if provider.name == "deepseek":
            if provider.api_key:
                os.environ["DEEPSEEK_API_KEY"] = provider.api_key
            if provider.base_url:
                # LiteLLM expects the base URL without /v1 suffix for DeepSeek
                base_url = provider.base_url.rstrip("/")
                if base_url.endswith("/v1"):
                    base_url = base_url[:-3]
                os.environ["DEEPSEEK_API_BASE"] = base_url
                logger.debug(f"Set DEEPSEEK_API_BASE={base_url}")
        
        # Setup OpenAI environment (used by default)
        elif provider.name == "openai":
            if provider.api_key:
                os.environ["OPENAI_API_KEY"] = provider.api_key
            if provider.base_url:
                os.environ["OPENAI_API_BASE"] = provider.base_url

    def _build_llm_string(self, model_override: Optional[str] = None) -> str:
        """Build LiteLLM-compatible model string."""
        settings = get_settings()
        provider = self._registry.get(settings.ai.default_provider)
        model = model_override or provider.model
        
        # For DeepSeek, use deepseek/model format with env vars
        if provider.name == "deepseek":
            model_name = model or "deepseek-chat"
            return f"deepseek/{model_name}"
        
        # For OpenAI and similar, use model name directly
        elif provider.name in ["openai", "anthropic", "cohere"]:
            return model
        
        # For other providers, use provider/model format
        else:
            return f"{provider.name}/{model}"

    def _build_agent(self, name: str, role: str, goal: str, backstory: str, model_override: Optional[str] = None) -> Agent:
        llm_str = self._build_llm_string(model_override)
        logger.debug(f"Building agent '{name}' with LLM: {llm_str}")
        
        # Import LiteLLM's ChatLiteLLM for proper LLM object
        try:
            from langchain_community.chat_models import ChatLiteLLM
            llm_obj = ChatLiteLLM(model=llm_str, temperature=0.7)
        except ImportError:
            # Fallback to string if langchain_community not available
            logger.warning("langchain_community not available, using string for LLM")
            llm_obj = llm_str
        
        return Agent(
            role=role,
            goal=goal,
            backstory=backstory,
            verbose=True,
            allow_delegation=False,
            llm=llm_obj,
        )

    def build_filtering_crew(self, context: Dict[str, Any], documents: List[Dict[str, Any]]) -> Crew:
        """Build crew for document filtering with structured output."""
        settings = get_settings()
        
        # 获取任务级别的AI配置，如果有的话
        ai_config = context.get("ai_config") or {}
        filter_model = ai_config.get("model") if ai_config.get("model") else settings.ai.filter_model
        
        analyst = self._build_agent(
            name="filtering-analyst",
            role="文献筛选分析师",
            goal="基于用户 prompt 和关键词，从候选文献信息中筛选最相关的文献，并提供结构化结论",
            backstory="你擅长理解科研需求，并准确判断文献是否匹配研究主题。",
            model_override=filter_model,
        )
        
        # Build document context string
        docs_text = "\n".join([
            f"[{i+1}] ID: {doc.get('external_id', '')}\n标题: {doc.get('title', '')}\n摘要: {doc.get('abstract', '')[:200]}..."
            for i, doc in enumerate(documents[:20])  # Limit context size
        ])
        
        prompt = context.get("prompt", "")
        keywords = ", ".join(context.get("keywords", []))
        
        # 获取自定义筛选提示词，如果没有则使用默认提示词
        filter_config = context.get("filter_config") or {}
        custom_filter_prompt = ""
        if isinstance(filter_config, dict):
            prompt_value = filter_config.get("filter_prompt")
            if prompt_value:
                custom_filter_prompt = str(prompt_value).strip()
        
                # 使用自定义提示词或默认提示词
                evaluation_guide = custom_filter_prompt if custom_filter_prompt else DEFAULT_FILTER_PROMPT
        
        filter_task = Task(
            description=f"""
任务：从以下候选文献中筛选与研究主题相关的文献。

研究主题: {prompt}
关键词: {keywords}

候选文献:
{docs_text}

{evaluation_guide}

输出格式必须是有效的 JSON 数组。
""",
            expected_output="""JSON array of filtered documents:
[
  {
    "external_id": "document_id",
    "is_selected": true,
    "score": 0.85,
    "summary": "简短总结",
    "highlights": ["亮点1", "亮点2"]
  }
]""",
            agent=analyst,
        )
        
        crew = Crew(
            agents=[analyst],
            tasks=[filter_task],
            process=Process.sequential,
            verbose=True,
        )
        return crew

    def build_single_doc_filtering_crew(self, context: Dict[str, Any], document: Dict[str, Any]) -> Crew:
        """Build crew for filtering a single document with full abstract access."""
        settings = get_settings()
        
        # 获取任务级别的AI配置，如果有的话
        ai_config = context.get("ai_config") or {}
        filter_model = ai_config.get("model") if ai_config.get("model") else settings.ai.filter_model
        
        analyst = self._build_agent(
            name="single-doc-analyst",
            role="文献相关性评估专家",
            goal="基于用户需求仔细阅读文献完整信息，评估其与研究主题的相关性",
            backstory="你是经验丰富的文献筛选专家，擅长理解科研需求并准确判断文献价值。你会仔细阅读文献的完整摘要和详细信息。",
            model_override=filter_model,
        )
        
        # Build full document context with complete information
        doc_title = document.get("title", "无标题")
        doc_abstract = document.get("abstract", "无摘要")
        doc_authors = ", ".join(document.get("authors", [])[:10]) if document.get("authors") else "未知作者"
        doc_keywords = ", ".join(document.get("keywords", [])) if document.get("keywords") else "无关键词"
        
        # 安全地提取年份
        published_at = document.get("published_at")
        if published_at:
            if hasattr(published_at, "year"):
                # datetime对象
                doc_year = str(published_at.year)
            elif isinstance(published_at, str):
                # 字符串，尝试提取前4个字符
                doc_year = published_at[:4] if len(published_at) >= 4 else published_at
            else:
                doc_year = str(published_at)[:4]
        else:
            doc_year = "未知年份"
        
        doc_citations = document.get("citation_count", "N/A")
        doc_id = document.get("external_id", "")
        
        prompt = context.get("prompt", "")
        keywords = ", ".join(context.get("keywords", []))
        
        # 获取自定义筛选提示词，如果没有则使用默认提示词
        filter_config = context.get("filter_config") or {}
        custom_filter_prompt = ""
        if isinstance(filter_config, dict):
            prompt_value = filter_config.get("filter_prompt")
            if prompt_value:
                custom_filter_prompt = str(prompt_value).strip()

        # 使用自定义提示词或默认提示词
        evaluation_guide = custom_filter_prompt if custom_filter_prompt else DEFAULT_FILTER_PROMPT
        
        filter_task = Task(
            description=f"""
任务：评估以下文献与研究主题的相关性。

研究主题: {prompt}
关键词: {keywords}

【待评估文献】
文献ID: {doc_id}
标题: {doc_title}
作者: {doc_authors}
发表年份: {doc_year}
引用次数: {doc_citations}
关键词: {doc_keywords}

完整摘要:
{doc_abstract}

{evaluation_guide}

**输出要求：**
- 必须是有效的JSON对象
- summary 和 highlights 必须使用中文
- 仔细阅读完整摘要后再做出判断
""",
            expected_output="""{
  "external_id": "document_id",
  "is_selected": true,
  "score": 0.85,
  "summary": "（中文）文献核心内容总结，说明选择或不选择的理由",
  "highlights": ["（中文）关键发现1", "（中文）关键发现2", "（中文）创新点3"]
}""",
            agent=analyst,
        )
        
        crew = Crew(
            agents=[analyst],
            tasks=[filter_task],
            process=Process.sequential,
            verbose=True,
        )
        return crew

    def build_coarse_filtering_crew(self, context: Dict[str, Any], documents: List[Dict[str, Any]]) -> Crew:
        """Build crew for coarse filtering - quick screening based on titles."""
        settings = get_settings()
        
        ai_config = context.get("ai_config") or {}
        filter_model = ai_config.get("model") if ai_config.get("model") else settings.ai.filter_model
        
        analyst = self._build_agent(
            name="coarse-filter-analyst",
            role="文献快速筛选专家",
            goal="根据标题和简短摘要快速判断文献是否可能与研究主题相关",
            backstory="你擅长快速浏览大量文献，根据标题和关键信息快速判断文献是否值得深入阅读。对于不确定的文献，倾向于保留。",
            model_override=filter_model,
        )
        
        # Build compact document list (titles + short abstract)
        docs_text = "\n".join([
            f"[{i+1}] ID: {doc.get('external_id', '')}\n标题: {doc.get('title', '无标题')}\n摘要: {doc.get('abstract', '')[:150]}..."
            for i, doc in enumerate(documents)
        ])
        
        prompt = context.get("prompt", "")
        keywords = ", ".join(context.get("keywords", []))
        
        filter_task = Task(
            description=f"""
任务：快速筛选以下候选文献，排除明显不相关的文献。

研究主题: {prompt}
关键词: {keywords}

候选文献（共{len(documents)}篇）:
{docs_text}

**筛选标准：**
1. 标题是否与研究主题有明显关联
2. 摘要中是否包含相关的关键词或概念
3. **宁可误保留，不要误排除** - 对于不确定的文献，设置 is_selected=true

**评分标准（粗筛）：**
- 0.6-1.0: 可能相关，保留
- 0.3-0.6: 不确定，保留
- 0.0-0.3: 明显不相关，排除

**输出要求：**
- 返回一个 JSON 数组
- 每篇文献都需要给出结果
- 粗筛阶段不需要 summary 和 highlights，可以为空
""",
            expected_output="""[
  {"external_id": "id1", "is_selected": true, "score": 0.7, "summary": "", "highlights": []},
  {"external_id": "id2", "is_selected": false, "score": 0.2, "summary": "", "highlights": []},
  ...
]""",
            agent=analyst,
        )
        
        crew = Crew(
            agents=[analyst],
            tasks=[filter_task],
            process=Process.sequential,
            verbose=True,
        )
        return crew

    def build_fine_filtering_crew(self, context: Dict[str, Any], documents: List[Dict[str, Any]]) -> Crew:
        """Build crew for fine filtering - detailed evaluation of multiple documents."""
        settings = get_settings()
        
        ai_config = context.get("ai_config") or {}
        filter_model = ai_config.get("model") if ai_config.get("model") else settings.ai.filter_model
        
        analyst = self._build_agent(
            name="fine-filter-analyst",
            role="文献精细评估专家",
            goal="仔细阅读文献的完整摘要，精确评估其与研究主题的相关性",
            backstory="你是经验丰富的科研人员，擅长深入分析文献内容，准确判断其学术价值和与研究主题的相关程度。",
            model_override=filter_model,
        )
        
        # Build detailed document context
        docs_text = "\n\n---\n\n".join([
            f"【文献 {i+1}】\n"
            f"ID: {doc.get('external_id', '')}\n"
            f"标题: {doc.get('title', '无标题')}\n"
            f"作者: {', '.join(doc.get('authors', [])[:5]) if doc.get('authors') else '未知'}\n"
            f"关键词: {', '.join(doc.get('keywords', [])) if doc.get('keywords') else '无'}\n"
            f"完整摘要:\n{doc.get('abstract', '无摘要')}"
            for i, doc in enumerate(documents)
        ])
        
        prompt = context.get("prompt", "")
        keywords = ", ".join(context.get("keywords", []))
        
        # 获取自定义筛选提示词
        filter_config = context.get("filter_config") or {}
        custom_filter_prompt = ""
        if isinstance(filter_config, dict):
            prompt_value = filter_config.get("filter_prompt")
            if prompt_value:
                custom_filter_prompt = str(prompt_value).strip()
        
        evaluation_guide = custom_filter_prompt if custom_filter_prompt else DEFAULT_FILTER_PROMPT
        
        filter_task = Task(
            description=f"""
任务：精细评估以下{len(documents)}篇文献与研究主题的相关性。

研究主题: {prompt}
关键词: {keywords}

{docs_text}

{evaluation_guide}

**输出要求：**
- 返回一个 JSON 数组，包含所有 {len(documents)} 篇文献的评估结果
- 每篇文献都需要提供 summary（中文总结）和 highlights（中文亮点）
- 仔细阅读每篇文献的完整摘要后再做判断
""",
            expected_output="""[
  {
    "external_id": "id1",
    "is_selected": true,
    "score": 0.85,
    "summary": "（中文）该文献的核心内容和选择理由",
    "highlights": ["亮点1", "亮点2", "亮点3"]
  },
  ...
]""",
            agent=analyst,
        )
        
        crew = Crew(
            agents=[analyst],
            tasks=[filter_task],
            process=Process.sequential,
            verbose=True,
        )
        return crew

    def build_summary_crew(self, context: Dict[str, Any], documents: List[Dict[str, Any]]) -> Crew:
        """Build crew for document summarization with trend analysis and custom templates."""
        settings = get_settings()
        
        # 获取任务级别的AI配置，如果有的话
        ai_config = context.get("ai_config") or {}
        summary_model = ai_config.get("model") if ai_config.get("model") else settings.ai.summary_model
        
        strategist = self._build_agent(
            name="summary-strategist",
            role="科研趋势分析师",
            goal="针对选定文献生成整合总结，并分析研究趋势和关键发现",
            backstory="你是经验丰富的科研趋势分析专家，擅长从大量文献中提炼核心观点，识别研究趋势，并为科研人员提供前瞻性洞察。",
            model_override=summary_model,
        )
        
        # Build document summary context (top 15 by score)
        sorted_docs = sorted(documents, key=lambda d: d.get("score", 0), reverse=True)
        docs_summary = "\n\n".join([
            f"[{i+1}] {doc.get('title', '无标题')} (相关性: {doc.get('score', 0):.2f})\n"
            f"作者: {', '.join(doc.get('authors', [])[:3]) if doc.get('authors') else '未知'}\n"
            f"摘要: {doc.get('abstract', '无摘要')[:300]}...\n"
            f"关键词: {', '.join(doc.get('keywords', [])[:5])}\n"
            f"亮点: {'; '.join(doc.get('highlights', [])[:3])}"
            for i, doc in enumerate(sorted_docs[:15])
        ])
        
        prompt = context.get("prompt", "")
        
        # 获取自定义总结提示词，如果没有则使用默认提示词
        summary_config = context.get("summary_config") or {}
        custom_summary_prompt = ""
        if isinstance(summary_config, dict):
            prompt_value = summary_config.get("summary_prompt")
            if prompt_value:
                custom_summary_prompt = str(prompt_value).strip()

        # 使用自定义提示词或默认提示词
        analysis_guide = custom_summary_prompt if custom_summary_prompt else DEFAULT_SUMMARY_PROMPT
        
        # Base task description
        task_desc = f"""
任务：对筛选后的高相关性文献进行深度分析和综合总结。

**重要：所有分析内容必须使用中文**

研究主题: {prompt}
文献总数: {len(documents)}

Top 相关文献（按评分排序）:
{docs_summary}

{analysis_guide}

**输出要求：所有文本内容（trend_summary, reason, description, key_insights, research_directions）必须使用中文**
"""
        
        expected_output = """{
  "trend_summary": "（中文）详细的趋势总结（2-3段落）...",
  "rankings": [
    {
      "title": "文献标题",
      "score": 0.95,
      "reason": "（中文）核心贡献和推荐理由",
      "external_id": "paper_id"
    }
  ],
  "sections": [
    {
      "category": "研究主题或方法分类",
      "papers": ["文献标题1", "文献标题2"],
      "description": "（中文）该类别的简要描述"
    }
  ],
  "key_insights": [
    "（中文）关键发现1",
    "（中文）关键发现2"
  ],
  "research_directions": [
    "（中文）未来研究方向1",
    "（中文）未来研究方向2"
  ]
}"""
        
        summary_task = Task(
            description=task_desc,
            expected_output=expected_output,
            agent=strategist,
        )
        
        crew = Crew(
            agents=[strategist],
            tasks=[summary_task],
            process=Process.sequential,
            verbose=True,
        )
        return crew
