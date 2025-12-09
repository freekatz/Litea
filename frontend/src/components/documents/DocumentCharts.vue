<template>
  <div class="charts-panel">
    <!-- 统计概览 - 移到最上面 -->
    <div class="chart-card">
      <h3>统计概览</h3>
      <div class="chart-content stats-grid">
        <div class="stat-item">
          <div class="stat-label">总文献数</div>
          <div class="stat-value">{{ overviewData.totalDocuments }}</div>
        </div>
        <div class="stat-item">
          <div class="stat-label">数据来源</div>
          <div class="stat-value">{{ sourceStats.length }}</div>
        </div>
        <div class="stat-item">
          <div class="stat-label">平均相关度</div>
          <div class="stat-value">{{ overviewData.avgScore }}%</div>
        </div>
        <div class="stat-item">
          <div class="stat-label">本周新增</div>
          <div class="stat-value">{{ overviewData.weekCount }}</div>
        </div>
      </div>
    </div>

    <div class="chart-card">
      <h3>来源分布</h3>
      <div class="chart-content">
        <div v-if="sourceStats.length === 0" class="empty-chart">暂无数据</div>
        <div v-else class="bar-chart">
          <div
            v-for="stat in sourceStats"
            :key="stat.source"
            class="bar-item"
          >
            <div class="bar-label">{{ stat.source }}</div>
            <div class="bar-wrapper">
              <div
                class="bar-fill"
                :style="{ width: (stat.count / maxCount * 100) + '%' }"
              ></div>
              <span class="bar-value">{{ stat.count }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div class="chart-card">
      <h3>时间趋势</h3>
      <div class="chart-content">
        <div v-if="timeStats.length === 0" class="empty-chart">暂无数据</div>
        <div v-else class="line-chart">
          <div
            v-for="stat in timeStats"
            :key="stat.date"
            class="time-item"
          >
            <div class="time-label">{{ stat.label }}</div>
            <div class="time-bar">
              <div
                class="time-fill"
                :style="{ height: (stat.count / maxTimeCount * 100) + '%' }"
              ></div>
            </div>
            <div class="time-value">{{ stat.count }}</div>
          </div>
        </div>
      </div>
    </div>

    <div class="chart-card">
      <h3>相关度分布</h3>
      <div class="chart-content">
        <div v-if="scoreStats.length === 0" class="empty-chart">暂无数据</div>
        <div v-else class="score-chart">
          <div
            v-for="stat in scoreStats"
            :key="stat.range"
            class="score-item"
          >
            <div class="score-label">{{ stat.range }}</div>
            <div class="score-bar">
              <div
                class="score-fill"
                :style="{ width: (stat.count / maxScoreCount * 100) + '%' }"
              ></div>
            </div>
            <div class="score-value">{{ stat.count }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { analyticsApi } from '@/api/analytics'

interface Props {
  taskId?: number | null
}

const props = defineProps<Props>()

// 后端返回的数据
const overviewData = ref({
  totalDocuments: 0,
  weekCount: 0,
  avgScore: 0
})

const sourceStats = ref<Array<{ source: string; count: number }>>([])
const timeStats = ref<Array<{ date: string; label: string; count: number }>>([])
const scoreStats = ref<Array<{ range: string; count: number }>>([])

const maxCount = computed(() => {
  return Math.max(...sourceStats.value.map(s => s.count), 1)
})

const maxTimeCount = computed(() => {
  return Math.max(...timeStats.value.map(s => s.count), 1)
})

const maxScoreCount = computed(() => {
  return Math.max(...scoreStats.value.map(s => s.count), 1)
})

async function loadStats() {
  try {
    const taskId = props.taskId ?? undefined
    
    console.log('=== DocumentCharts loadStats ===')
    console.log('taskId:', taskId)
    
    // 并行加载所有统计数据
    const [overviewRes, sourcesRes, trendsRes, scoresRes] = await Promise.all([
      analyticsApi.getOverview(taskId),
      analyticsApi.getSources(taskId),
      analyticsApi.getTrends(7, taskId),
      analyticsApi.getScores(taskId)
    ])
    
    console.log('overviewRes:', JSON.stringify(overviewRes, null, 2))
    console.log('sourcesRes:', JSON.stringify(sourcesRes, null, 2))
    
    // 处理概览数据
    if (overviewRes?.data) {
      overviewData.value = {
        totalDocuments: overviewRes.data.total_documents || 0,
        weekCount: overviewRes.data.documents_this_week || 0,
        avgScore: Math.round(overviewRes.data.avg_citations || 0)
      }
      console.log('overviewData set to:', overviewData.value)
    } else {
      console.log('overviewRes.data is null/undefined')
    }
    
    // 处理来源分布
    if (sourcesRes?.data?.sources) {
      sourceStats.value = sourcesRes.data.sources
    }
    
    // 处理时间趋势 - 补全最近7天
    const trendsMap = new Map<string, number>()
    const now = new Date()
    for (let i = 6; i >= 0; i--) {
      const date = new Date(now)
      date.setDate(date.getDate() - i)
      const dateStr = date.toISOString().split('T')[0]
      trendsMap.set(dateStr, 0)
    }
    
    if (trendsRes?.data?.trends) {
      for (const item of trendsRes.data.trends) {
        if (trendsMap.has(item.date)) {
          trendsMap.set(item.date, item.count)
        }
      }
    }
    
    timeStats.value = Array.from(trendsMap.entries()).map(([date, count]) => ({
      date,
      label: new Date(date).getMonth() + 1 + '/' + new Date(date).getDate(),
      count
    }))
    
    // 处理相关度分布
    if (scoresRes?.data) {
      overviewData.value.avgScore = Math.round(scoresRes.data.avg_score || 0)
      scoreStats.value = scoresRes.data.distribution || []
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

// 监听任务变化，重新加载数据
watch(() => props.taskId, () => {
  loadStats()
})

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.charts-panel {
  min-width: 280px;
  max-width: 500px;
  background: white;
  border-left: 1px solid #e5e7eb;
  overflow-y: auto;
  padding: 16px;
  flex-shrink: 0;
}

.chart-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
}

.chart-card h3 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.chart-content {
  min-height: 80px;
}

.empty-chart {
  text-align: center;
  color: #9ca3af;
  padding: 32px 0;
  font-size: 13px;
}

/* 柱状图 */
.bar-chart {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.bar-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.bar-label {
  width: 80px;
  font-size: 12px;
  color: #6b7280;
  text-align: right;
  flex-shrink: 0;
}

.bar-wrapper {
  flex: 1;
  position: relative;
  height: 24px;
  background: #f3f4f6;
  border-radius: 4px;
  overflow: hidden;
}

.bar-fill {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  background: linear-gradient(90deg, #3b82f6 0%, #2563eb 100%);
  transition: width 0.3s ease;
}

.bar-value {
  position: absolute;
  right: 6px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 11px;
  font-weight: 600;
  color: #374151;
}

/* 时间趋势图 */
.line-chart {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 4px;
  height: 100px;
}

.time-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
}

.time-bar {
  width: 100%;
  height: 60px;
  background: #f3f4f6;
  border-radius: 4px 4px 0 0;
  position: relative;
  display: flex;
  align-items: flex-end;
}

.time-fill {
  width: 100%;
  background: linear-gradient(180deg, #10b981 0%, #059669 100%);
  border-radius: 4px 4px 0 0;
  transition: height 0.3s ease;
  min-height: 2px;
}

.time-label {
  font-size: 10px;
  color: #9ca3af;
}

.time-value {
  font-size: 11px;
  font-weight: 600;
  color: #374151;
}

/* 相关度分布 */
.score-chart {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.score-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.score-label {
  width: 60px;
  font-size: 12px;
  color: #6b7280;
  text-align: right;
  flex-shrink: 0;
}

.score-bar {
  flex: 1;
  height: 20px;
  background: #f3f4f6;
  border-radius: 4px;
  position: relative;
}

.score-fill {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  background: linear-gradient(90deg, #f59e0b 0%, #d97706 100%);
  border-radius: 4px;
  transition: width 0.3s ease;
}

.score-value {
  width: 30px;
  text-align: right;
  font-size: 11px;
  font-weight: 600;
  color: #374151;
}

/* 统计概览 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
}

.stat-item {
  text-align: center;
  padding: 12px;
  background: #f9fafb;
  border-radius: 6px;
}

.stat-label {
  font-size: 11px;
  color: #6b7280;
  margin-bottom: 6px;
}

.stat-value {
  font-size: 20px;
  font-weight: 700;
  color: #3b82f6;
}
</style>
