import staticConstants from '@shared/config/constants.json'

type StaticOption = {
  value: string
  label: string
  icon?: string
  [key: string]: unknown
}

type FilterDefaults = {
  min_relevance_score?: number
  max_documents_per_source?: number
  [key: string]: unknown
}

type StaticConfigShape = {
  task_statuses?: StaticOption[]
  notification_channels?: StaticOption[]
  document_sort_options?: StaticOption[]
  summary_display_modes?: StaticOption[]
  ai_providers?: StaticOption[]
  retrieval_sources?: StaticOption[]
  filter_defaults?: FilterDefaults
  prompts?: Record<string, string>
}

const definitions = staticConstants as StaticConfigShape

const FALLBACK_FILTER_PROMPT = `请仔细阅读文献的完整信息，特别是摘要部分，然后评估：

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
  - 与研究主题最相关的部分`

const FALLBACK_SUMMARY_PROMPT = `对筛选后的文献进行深度分析和综合总结。

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
  - 3-5个方向`

const promptTemplates: Record<string, string> = definitions.prompts ?? {}

export const taskStatusOptions: StaticOption[] = definitions.task_statuses ?? []
export const notificationChannels: StaticOption[] = definitions.notification_channels ?? []
export const documentSortOptions: StaticOption[] = definitions.document_sort_options ?? []
export const summaryDisplayModes: StaticOption[] = definitions.summary_display_modes ?? []
export const aiProviderOptions: StaticOption[] = definitions.ai_providers ?? []
export const retrievalSourceOptions: StaticOption[] = definitions.retrieval_sources ?? []
export const filterDefaults: FilterDefaults = definitions.filter_defaults ?? {}
export const defaultFilterPrompt: string = promptTemplates.filter_default ?? FALLBACK_FILTER_PROMPT
export const defaultSummaryPrompt: string = promptTemplates.summary_default ?? FALLBACK_SUMMARY_PROMPT

export const taskStatusLabelMap: Record<string, string> = Object.fromEntries(
  taskStatusOptions.map(option => [option.value, option.label])
)

export const notificationChannelIconMap: Record<string, string | undefined> = Object.fromEntries(
  notificationChannels.map(option => [option.value, typeof option.icon === 'string' ? option.icon : undefined])
)
