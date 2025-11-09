<template>
  <div class="modal-overlay" @click.self="handleClose">
    <div class="modal-container">
      <div class="modal-header">
        <h2>{{ (task && (task as any).id) ? '编辑任务' : '创建任务' }}</h2>
        <button type="button" @click="handleClose" class="btn-close">×</button>
      </div>

      <form @submit.prevent="handleSubmit" class="modal-body">
        <!-- 任务名称 -->
        <div class="form-group">
          <label>任务名称 *</label>
          <input
            v-model="form.name"
            type="text"
            required
            placeholder="例如：追踪大语言模型最新研究"
            class="form-input"
          />
        </div>

        <!-- 研究主题 -->
        <div class="form-group">
          <label>研究主题 (Prompt) *</label>
          <textarea
            v-model="form.prompt"
            required
            rows="3"
            placeholder="描述你的研究兴趣"
            class="form-input"
          ></textarea>
          <button
            type="button"
            @click="extractKeywords"
            :disabled="!form.prompt || extracting"
            class="btn-ai"
          >
            {{ extracting ? '提取中...' : '🤖 AI 提取关键词' }}
          </button>
        </div>

        <!-- 关键词 -->
        <div class="form-group">
          <label>关键词</label>
          <div class="keyword-input">
            <input
              v-model="newKeyword"
              @keyup.enter="addKeyword"
              type="text"
              placeholder="输入关键词后按回车"
              class="form-input"
            />
            <button type="button" @click="addKeyword" class="btn-add">+</button>
          </div>
          <div v-if="form.keywords.length" class="keyword-list">
            <div
              v-for="(kw, idx) in form.keywords"
              :key="idx"
              class="keyword-chip"
            >
              <input
                v-if="editingKeywordIndex === idx"
                v-model="editingKeywordValue"
                @keyup.enter="saveKeyword(idx)"
                @blur="saveKeyword(idx)"
                @keyup.esc="cancelEditKeyword"
                ref="keywordInput"
                class="keyword-edit-input"
                type="text"
              />
              <span v-else @click="startEditKeyword(idx, kw)" class="keyword-text">
                {{ kw }}
              </span>
              <button type="button" @click="removeKeyword(idx)" class="chip-remove">×</button>
            </div>
          </div>
        </div>

        <!-- 数据来源 -->
        <div class="form-group">
          <label>数据来源</label>
          <label class="checkbox-label">
            <input v-model="sourceArxiv" type="checkbox" />
            <span>arXiv</span>
          </label>
        </div>

        <!-- 运行时间 -->
        <div class="form-group">
          <label>每日运行时间</label>
          <div class="time-input">
            <input
              v-model.number="form.run_at_hour"
              type="number"
              min="0"
              max="23"
              class="form-input-sm"
            />
            <span>:</span>
            <input
              v-model.number="form.run_at_minute"
              type="number"
              min="0"
              max="59"
              class="form-input-sm"
            />
          </div>
        </div>

        <!-- 通知推送配置 -->
        <div class="form-group">
          <div class="config-section">
            <button type="button" @click="showNotificationConfig = !showNotificationConfig" class="section-toggle">
              <span class="config-icon">📬</span> {{ showNotificationConfig ? '▼' : '▶' }} 通知推送配置
            </button>
            
            <div v-if="showNotificationConfig" class="config-panels">
              <div class="config-panel">
                <div class="form-group">
                  <label>推送渠道</label>
                  <div class="checkbox-group">
                    <label class="checkbox-label">
                      <input 
                        type="checkbox" 
                        value="email" 
                        v-model="form.notification.channels" 
                      />
                      📧 邮件推送
                    </label>
                    <label class="checkbox-label">
                      <input 
                        type="checkbox" 
                        value="feishu" 
                        v-model="form.notification.channels" 
                      />
                      🔔 飞书群机器人
                    </label>
                  </div>
                </div>
                
                <!-- 邮件配置 -->
                <div v-if="form.notification.channels.includes('email')" class="notification-channel-config">
                    <h5>📧 邮件配置</h5>
                    <div class="form-group">
                      <label>接收人邮箱 (多个邮箱用逗号分隔)</label>
                      <input
                        v-model="emailRecipientsInput"
                        type="text"
                        placeholder="user@example.com, admin@example.com"
                        class="form-input"
                      />
                    </div>
                    <div class="form-group">
                      <label>邮件主题模板 (可选)</label>
                      <input
                        v-model="form.notification.email_subject_template"
                        type="text"
                        placeholder="留空使用默认: 【{任务名}】文献推送"
                        class="form-input"
                      />
                    </div>
                  </div>
                  
                  <!-- 飞书配置 -->
                  <div v-if="form.notification.channels.includes('feishu')" class="notification-channel-config">
                    <h5>🔔 飞书群机器人配置</h5>
                    <div class="form-group">
                      <label>Webhook URL</label>
                      <input
                        v-model="form.notification.feishu_webhook_url"
                        type="url"
                        placeholder="https://open.feishu.cn/open-apis/bot/v2/hook/..."
                        class="form-input"
                      />
                      <div class="hint-text">
                        获取方式: 飞书群 → 设置 → 群机器人 → 添加机器人 → 自定义机器人 → 复制Webhook地址
                      </div>
                    </div>
                  </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 高级配置 -->
        <div class="form-group">
          <div class="config-section">
            <button type="button" @click="showAdvancedConfig = !showAdvancedConfig" class="section-toggle">
              {{ showAdvancedConfig ? '▼' : '▶' }} 高级配置（AI模型、筛选、总结）
            </button>
            
            <div v-if="showAdvancedConfig" class="config-panels">
              <!-- AI模型配置 -->
              <div class="config-panel">
                <h4><span class="config-icon">🤖</span> AI模型配置</h4>
                <div class="form-row">
                  <div class="form-col">
                    <label>提供商</label>
                    <select v-model="form.ai_config.provider" class="form-input">
                      <option value="deepseek">DeepSeek</option>
                      <option value="openai">OpenAI</option>
                      <option value="doubao">豆包</option>
                      <option value="qwen">通义千问</option>
                    </select>
                  </div>
                  <div class="form-col">
                    <label>模型</label>
                    <input v-model="form.ai_config.model" type="text" placeholder="deepseek-chat" class="form-input" />
                  </div>
                </div>
                <div class="form-row">
                  <div class="form-col">
                    <label>温度 (0-2)</label>
                    <input v-model.number="form.ai_config.temperature" type="number" min="0" max="2" step="0.1" class="form-input" />
                  </div>
                  <div class="form-col">
                    <label>最大Token数</label>
                    <input v-model.number="form.ai_config.max_tokens" type="number" placeholder="可选" class="form-input" />
                  </div>
                </div>
              </div>

              <!-- 文献筛选配置 -->
              <div class="config-panel">
                <h4><span class="config-icon">🔍</span> 文献筛选配置</h4>
                <div class="form-row">
                  <label class="checkbox-label">
                    <input v-model="form.filter_config.enabled" type="checkbox" />
                    <span>启用AI筛选</span>
                  </label>
                </div>
                <div class="form-row">
                  <div class="form-col">
                    <label>最低相关度阈值 (0-1)</label>
                    <input v-model.number="form.filter_config.min_relevance_score" type="number" min="0" max="1" step="0.1" class="form-input" />
                  </div>
                  <div class="form-col">
                    <label>每来源最多文献数</label>
                    <input v-model.number="form.filter_config.max_documents_per_source" type="number" min="1" max="200" class="form-input" />
                  </div>
                </div>
                <div class="form-group">
                  <label>
                    筛选提示词
                    <button type="button" @click="resetFilterPrompt" class="btn-reset" title="恢复默认提示词">🔄</button>
                  </label>
                  <textarea
                    v-model="form.filter_config.filter_prompt"
                    rows="6"
                    :placeholder="defaultFilterPrompt"
                    class="form-input prompt-textarea"
                  ></textarea>
                  <div class="hint-text">留空则使用默认提示词。AI将基于此提示词筛选文献。</div>
                </div>
              </div>

              <!-- 文献总结配置 -->
              <div class="config-panel">
                <h4><span class="config-icon">📝</span> 文献总结配置</h4>
                <div class="form-row">
                  <label class="checkbox-label">
                    <input v-model="form.summary_config.enabled" type="checkbox" />
                    <span>启用AI总结</span>
                  </label>
                </div>
                <div class="form-row">
                  <label class="checkbox-label">
                    <input v-model="form.summary_config.generate_individual_summary" type="checkbox" />
                    <span>生成独立总结</span>
                  </label>
                  <label class="checkbox-label">
                    <input v-model="form.summary_config.generate_overall_summary" type="checkbox" />
                    <span>生成整体总结</span>
                  </label>
                  <label class="checkbox-label">
                    <input v-model="form.summary_config.include_trends" type="checkbox" />
                    <span>包含趋势分析</span>
                  </label>
                </div>
                <div class="form-group">
                  <label>
                    总结提示词
                    <button type="button" @click="resetSummaryPrompt" class="btn-reset" title="恢复默认提示词">🔄</button>
                  </label>
                  <textarea
                    v-model="form.summary_config.summary_prompt"
                    rows="8"
                    :placeholder="defaultSummaryPrompt"
                    class="form-input prompt-textarea"
                  ></textarea>
                  <div class="hint-text">留空则使用默认提示词。AI将基于此提示词生成总结报告。</div>
                </div>
                <div class="form-row">
                  <div class="form-col">
                    <label>展示模式</label>
                    <select v-model="form.summary_config.display_mode" class="form-input">
                      <option value="grouped">按来源分组</option>
                      <option value="ranked">按排名展示</option>
                    </select>
                  </div>
                  <div class="form-col">
                    <label>{{ form.summary_config.display_mode === 'grouped' ? '每来源展示数' : 'Top N数量' }}</label>
                    <input 
                      v-if="form.summary_config.display_mode === 'grouped'"
                      v-model.number="form.summary_config.items_per_source" 
                      type="number" 
                      min="1" 
                      max="50" 
                      class="form-input" 
                    />
                    <input 
                      v-else
                      v-model.number="form.summary_config.top_n_ranked" 
                      type="number" 
                      min="1" 
                      max="100" 
                      class="form-input" 
                    />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button type="button" @click="handleClose" class="btn-cancel">取消</button>
          <button type="submit" :disabled="!canSubmit" class="btn-submit">保存</button>
          <button type="button" @click="handleSaveAndStart" :disabled="!canSubmit" class="btn-submit-primary">保存并启动</button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { tasksApi } from '@/api/tasks'

// 默认提示词常量
const defaultFilterPrompt = `请仔细阅读文献的完整信息，特别是摘要部分，然后评估：

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

const defaultSummaryPrompt = `对筛选后的文献进行深度分析和综合总结。

请从以下角度进行分析：

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

interface Task {
  id: number
  name: string
  prompt: string
  keywords: (string | { keyword: string; is_user_defined: boolean })[]
  data_sources: (string | { source_name: string; parameters: any })[]
  run_at_hour: number
  run_at_minute?: number
  notification?: any  // 后端返回的字段名
  notification_config?: any  // 向后兼容旧字段名
}

const props = defineProps<{
  task?: Task | null
}>()

const emit = defineEmits<{
  close: []
  saved: []
}>()

const form = ref({
  name: '',
  prompt: '',
  keywords: [] as string[],
  data_sources: [] as string[],
  run_at_hour: 9,
  run_at_minute: 0,
  notification_config: null as any,
  notification: {
    enabled: false,
    channels: [] as string[],
    email_recipients: [] as string[],
    email_subject_template: null as string | null,
    feishu_webhook_url: null as string | null,
    schedule: null as string | null,
    options: {} as any
  },
  ai_config: {
    provider: 'deepseek',
    model: 'deepseek-chat',
    temperature: 0.7,
    max_tokens: null as number | null
  },
  filter_config: {
    enabled: true,
    filter_prompt: null as string | null,
    min_relevance_score: 0.6,
    max_documents_per_source: 50
  },
  summary_config: {
    enabled: true,
    summary_prompt: null as string | null,
    generate_individual_summary: true,
    generate_overall_summary: true,
    display_mode: 'grouped',
    items_per_source: 5,
    top_n_ranked: 10,
    include_trends: true
  }
})

const newKeyword = ref('')
const emailRecipientsInput = ref('')
const sourceArxiv = ref(true)
const extracting = ref(false)
const editingKeywordIndex = ref<number | null>(null)
const editingKeywordValue = ref('')
const keywordInput = ref<HTMLInputElement[]>([])
const showAdvancedConfig = ref(false)
const showNotificationConfig = ref(false)

const canSubmit = computed(() => {
  return form.value.name.trim() !== '' && form.value.prompt.trim() !== ''
})

function handleClose() {
  emit('close')
}

function addKeyword() {
  if (newKeyword.value.trim()) {
    form.value.keywords.push(newKeyword.value.trim())
    newKeyword.value = ''
  }
}

function removeKeyword(index: number) {
  form.value.keywords.splice(index, 1)
}

function startEditKeyword(index: number, keyword: string) {
  editingKeywordIndex.value = index
  editingKeywordValue.value = keyword
  // 等待 DOM 更新后自动聚焦
  setTimeout(() => {
    const input = keywordInput.value[0]
    if (input) {
      input.focus()
      input.select()
    }
  }, 0)
}

function saveKeyword(index: number) {
  if (editingKeywordValue.value.trim()) {
    form.value.keywords[index] = editingKeywordValue.value.trim()
  }
  editingKeywordIndex.value = null
  editingKeywordValue.value = ''
}

function cancelEditKeyword() {
  editingKeywordIndex.value = null
  editingKeywordValue.value = ''
}

function resetFilterPrompt() {
  form.value.filter_config.filter_prompt = null
}

function resetSummaryPrompt() {
  form.value.summary_config.summary_prompt = null
}

async function extractKeywords() {
  if (!form.value.prompt) return
  extracting.value = true
  try {
    const response = await tasksApi.suggestKeywords({
      prompt: form.value.prompt,
      max_keywords: 10
    })
    const suggested = response.data || []
    suggested.forEach((kw: string) => {
      if (!form.value.keywords.includes(kw)) {
        form.value.keywords.push(kw)
      }
    })
  } catch (error) {
    console.error('Failed to extract keywords:', error)
  } finally {
    extracting.value = false
  }
}

async function handleSubmit() {
  if (!canSubmit.value) return

  // 准备数据源（字符串数组转对象数组）
  const sources = sourceArxiv.value ? [{
    source_name: 'arxiv',
    parameters: {}
  }] : []
  
  // 准备关键词（字符串数组转对象数组）
  const keywords = form.value.keywords.map(kw => ({
    keyword: kw,
    is_user_defined: true
  }))
  
  // 准备通知配置 - 使用新的notification结构
  const notification = {
    enabled: form.value.notification.channels.length > 0, // 自动根据是否选择渠道判断
    channels: form.value.notification.channels,
    email_recipients: emailRecipientsInput.value 
      ? emailRecipientsInput.value.split(',').map(e => e.trim()).filter(e => e)
      : [],
    email_subject_template: form.value.notification.email_subject_template || null,
    feishu_webhook_url: form.value.notification.feishu_webhook_url || null,
    schedule: null,
    options: {}
  }

  // 构建请求数据
  const taskData = {
    name: form.value.name,
    prompt: form.value.prompt,
    keywords: keywords,
    sources: sources,
    run_at_hour: form.value.run_at_hour,
    run_at_minute: form.value.run_at_minute,
    run_timezone: 'Asia/Shanghai',
    notification: notification,
    ai_config: form.value.ai_config,
    filter_config: form.value.filter_config,
    summary_config: form.value.summary_config
  }

  try {
    // 判断是更新还是创建：有task且有id才是更新
    if (props.task && (props.task as any).id) {
      await tasksApi.update((props.task as any).id, taskData)
    } else {
      await tasksApi.create(taskData)
    }
    emit('saved')
  } catch (error) {
    console.error('Failed to save task:', error)
    alert('保存失败，请重试')
  }
}

async function handleSaveAndStart() {
  if (!canSubmit.value) return

  // 准备数据源（字符串数组转对象数组）
  const sources = sourceArxiv.value ? [{
    source_name: 'arxiv',
    parameters: {}
  }] : []
  
  // 准备关键词（字符串数组转对象数组）
  const keywords = form.value.keywords.map(kw => ({
    keyword: kw,
    is_user_defined: true
  }))
  
  // 准备通知配置 - 使用新的notification结构
  const notification = {
    enabled: form.value.notification.channels.length > 0, // 自动根据是否选择渠道判断
    channels: form.value.notification.channels,
    email_recipients: emailRecipientsInput.value 
      ? emailRecipientsInput.value.split(',').map(e => e.trim()).filter(e => e)
      : [],
    email_subject_template: form.value.notification.email_subject_template || null,
    feishu_webhook_url: form.value.notification.feishu_webhook_url || null,
    schedule: null,
    options: {}
  }

  // 构建请求数据
  const taskData = {
    name: form.value.name,
    prompt: form.value.prompt,
    keywords: keywords,
    sources: sources,
    run_at_hour: form.value.run_at_hour,
    run_at_minute: form.value.run_at_minute,
    run_timezone: 'Asia/Shanghai',
    notification: notification,
    ai_config: form.value.ai_config,
    filter_config: form.value.filter_config,
    summary_config: form.value.summary_config
  }

  try {
    let taskId = (props.task as any)?.id
    // 判断是更新还是创建：有task且有id才是更新
    if (props.task && (props.task as any).id) {
      await tasksApi.update((props.task as any).id, taskData)
    } else {
      const response = await tasksApi.create(taskData)
      taskId = response.id
      console.log('任务创建成功, ID:', taskId)
    }
    
    // 保存成功后立即启动任务
    if (taskId) {
      console.log('正在启动任务:', taskId)
      await tasksApi.start(taskId)
      console.log('任务启动成功')
      // 等待一小段时间确保状态更新
      await new Promise(resolve => setTimeout(resolve, 500))
    }
    
    emit('saved')
  } catch (error) {
    console.error('Failed to save and start task:', error)
    alert('保存或启动失败，请重试')
  }
}

onMounted(() => {
  if (props.task) {
    form.value.name = props.task.name
    form.value.prompt = props.task.prompt
    
    // 处理 keywords - 可能是字符串数组或对象数组
    if (Array.isArray(props.task.keywords)) {
      form.value.keywords = props.task.keywords.map(kw => 
        typeof kw === 'string' ? kw : kw.keyword
      )
    } else {
      form.value.keywords = []
    }
    
    // 处理 data_sources - 可能是字符串数组或对象数组
    if (Array.isArray(props.task.data_sources)) {
      form.value.data_sources = props.task.data_sources.map(src =>
        typeof src === 'string' ? src : src.source_name
      )
      sourceArxiv.value = form.value.data_sources.includes('arxiv')
    } else {
      form.value.data_sources = []
      sourceArxiv.value = true  // 默认选中 arXiv
    }
    
    form.value.run_at_hour = props.task.run_at_hour || 9
    form.value.run_at_minute = props.task.run_at_minute || 0
    
    // 加载配置项（如果存在）
    if ((props.task as any).ai_config) {
      form.value.ai_config = { ...form.value.ai_config, ...(props.task as any).ai_config }
    }
    if ((props.task as any).filter_config) {
      form.value.filter_config = { ...form.value.filter_config, ...(props.task as any).filter_config }
    }
    if ((props.task as any).summary_config) {
      form.value.summary_config = { ...form.value.summary_config, ...(props.task as any).summary_config }
    }
    
    // 加载通知配置
    // 注意：后端返回的字段名是 notification，不是 notification_config
    const notificationData = (props.task as any).notification || props.task.notification_config
    if (notificationData) {
      const nc = notificationData as any
      form.value.notification.enabled = nc.enabled || false
      form.value.notification.channels = nc.channels || []
      form.value.notification.email_subject_template = nc.email_subject_template || null
      form.value.notification.feishu_webhook_url = nc.feishu_webhook_url || null
      
      // 加载邮件接收人
      if (nc.email_recipients && Array.isArray(nc.email_recipients)) {
        emailRecipientsInput.value = nc.email_recipients.join(', ')
      }
      
      // 保持向后兼容 - 从旧的recipients字段加载
      if (!emailRecipientsInput.value && nc.recipients?.length > 0) {
        emailRecipientsInput.value = nc.recipients.join(', ')
      }
    }
  } else {
    // 新建任务时，默认选中 arXiv
    sourceArxiv.value = true
  }
})
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  padding: 20px;
}

.modal-container {
  background: white;
  border-radius: 8px;
  box-shadow: 0 8px 16px rgba(0, 0, 0, 0.2);
  max-width: 1200px;
  width: 90%;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
}

/* 响应式调整 */
@media (max-width: 1400px) {
  .modal-container {
    max-width: 85%;
  }
}

@media (max-width: 1024px) {
  .modal-container {
    max-width: 95%;
    width: 95%;
  }
}

@media (max-width: 768px) {
  .modal-container {
    max-width: 100%;
    width: 100%;
    max-height: 100vh;
    border-radius: 0;
  }
}

.modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.btn-close {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  font-size: 24px;
  color: #6b7280;
  cursor: pointer;
  border-radius: 4px;
}

.btn-close:hover {
  background: #f3f4f6;
}

.modal-body {
  padding: 24px;
  overflow-y: auto;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 8px;
}

.form-input {
  width: 100%;
  padding: 8px 12px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 14px;
}

.form-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.btn-ai {
  margin-top: 8px;
  padding: 10px 16px;
  border: 1px solid #3b82f6;
  background: transparent;
  color: #3b82f6;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.2s;
}

.btn-ai:hover:not(:disabled) {
  background: #3b82f6;
  color: white;
}

.btn-ai:disabled {
  color: #9ca3af;
  border-color: #9ca3af;
  cursor: not-allowed;
}

.keyword-input {
  display: flex;
  gap: 8px;
}

.btn-add {
  width: 40px;
  padding: 8px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  font-size: 18px;
}

.btn-add:hover {
  background: #f9fafb;
}

.keyword-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.keyword-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: #e0e7ff;
  color: #3730a3;
  border-radius: 16px;
  font-size: 13px;
}

.keyword-text {
  cursor: pointer;
  user-select: none;
}

.keyword-text:hover {
  text-decoration: underline;
}

.keyword-edit-input {
  border: none;
  background: transparent;
  color: #3730a3;
  font-size: 13px;
  padding: 0;
  margin: 0;
  width: auto;
  min-width: 60px;
  outline: none;
  font-family: inherit;
}

.chip-remove {
  border: none;
  background: transparent;
  color: #6366f1;
  font-size: 16px;
  cursor: pointer;
  padding: 0;
  width: 16px;
  height: 16px;
  line-height: 1;
}

.chip-remove:hover {
  color: #4338ca;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.checkbox-label input {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.time-input {
  display: flex;
  align-items: center;
  gap: 8px;
}

.form-input-sm {
  width: 70px;
  padding: 8px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  font-size: 14px;
  text-align: center;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 12px;
  padding-top: 20px;
  border-top: 1px solid #e5e7eb;
}

.btn-cancel {
  padding: 8px 16px;
  border: 1px solid #d1d5db;
  border-radius: 4px;
  background: white;
  cursor: pointer;
  font-size: 14px;
}

.btn-cancel:hover {
  background: #f9fafb;
}

.btn-submit {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  background: #3b82f6;
  color: white;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
}

.btn-submit:hover:not(:disabled) {
  background: #2563eb;
}

.btn-submit:disabled {
  background: #9ca3af;
  cursor: not-allowed;
}

.btn-submit-primary {
  padding: 8px 16px;
  border: none;
  border-radius: 4px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  box-shadow: 0 4px 6px -1px rgba(102, 126, 234, 0.3);
  transition: all 0.2s ease;
}

.btn-submit-primary:hover:not(:disabled) {
  background: linear-gradient(135deg, #5a67d8 0%, #6b3fa0 100%);
  box-shadow: 0 6px 8px -1px rgba(102, 126, 234, 0.4);
  transform: translateY(-1px);
}

.btn-submit-primary:disabled {
  background: #9ca3af;
  cursor: not-allowed;
  box-shadow: none;
}

/* 配置面板样式 */
.config-section {
  margin-top: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  overflow: hidden;
}

.section-toggle {
  width: 100%;
  padding: 12px 16px;
  border: none;
  background: #f9fafb;
  text-align: left;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  transition: background 0.2s;
}

.section-toggle:hover {
  background: #f3f4f6;
}

.config-panels {
  padding: 16px;
  background: #fafbfc;
}

.config-panel {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 16px;
  margin-bottom: 16px;
}

.config-panel:last-child {
  margin-bottom: 0;
}

.config-panel h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  padding-bottom: 8px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  gap: 8px;
}

.config-icon {
  font-size: 20px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.form-row {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}

.form-row:last-child {
  margin-bottom: 0;
}

.form-col {
  flex: 1;
}

.form-col label {
  display: block;
  margin-bottom: 4px;
  font-size: 13px;
  color: #6b7280;
}

.form-row .checkbox-label {
  margin-right: 16px;
}

.prompt-textarea {
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 12px;
  line-height: 1.5;
  resize: vertical;
}

.config-panel label {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
  font-size: 13px;
  font-weight: 500;
  color: #374151;
}

.btn-reset {
  padding: 2px 8px;
  border: 1px solid #d1d5db;
  border-radius: 3px;
  background: white;
  color: #6b7280;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-reset:hover {
  background: #f3f4f6;
  color: #374151;
  border-color: #9ca3af;
}

.hint-text {
  margin-top: 4px;
  font-size: 12px;
  color: #9ca3af;
  font-style: italic;
}

.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #374151;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.notification-channel-config {
  margin-top: 16px;
  padding: 12px;
  background: #f9fafb;
  border-radius: 6px;
  border-left: 3px solid #3b82f6;
}

.notification-channel-config h5 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}
</style>

