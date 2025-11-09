<template>
  <div class="charts-panel">
    <!-- 统计概览 - 移到最上面 -->
    <div class="chart-card">
      <h3>统计概览</h3>
      <div class="chart-content stats-grid">
        <div class="stat-item">
          <div class="stat-label">总文献数</div>
          <div class="stat-value">{{ totalCount }}</div>
        </div>
        <div class="stat-item">
          <div class="stat-label">数据来源</div>
          <div class="stat-value">{{ sourceCount }}</div>
        </div>
        <div class="stat-item">
          <div class="stat-label">平均相关度</div>
          <div class="stat-value">{{ avgScore }}%</div>
        </div>
        <div class="stat-item">
          <div class="stat-label">本周新增</div>
          <div class="stat-value">{{ weekCount }}</div>
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
import { computed } from 'vue'

interface Document {
  id: number
  title: string
  source: string
  relevance_score?: number
  created_at: string
}

interface Props {
  documents: Document[]
}

const props = defineProps<Props>()

// 来源统计
const sourceStats = computed(() => {
  const stats = new Map<string, number>()
  props.documents.forEach(doc => {
    stats.set(doc.source, (stats.get(doc.source) || 0) + 1)
  })
  return Array.from(stats.entries())
    .map(([source, count]) => ({ source, count }))
    .sort((a, b) => b.count - a.count)
})

const maxCount = computed(() => {
  return Math.max(...sourceStats.value.map(s => s.count), 1)
})

// 时间趋势（最近7天）
const timeStats = computed(() => {
  const now = new Date()
  const stats = new Map<string, number>()
  
  // 初始化最近7天
  for (let i = 6; i >= 0; i--) {
    const date = new Date(now)
    date.setDate(date.getDate() - i)
    const dateStr = date.toISOString().split('T')[0]
    stats.set(dateStr, 0)
  }
  
  // 统计文献
  props.documents.forEach(doc => {
    if (doc.created_at) {
      try {
        const dateStr = doc.created_at.split('T')[0]
        if (stats.has(dateStr)) {
          stats.set(dateStr, (stats.get(dateStr) || 0) + 1)
        }
      } catch (error) {
        console.error('解析日期失败:', doc.created_at, error)
      }
    }
  })
  
  return Array.from(stats.entries())
    .map(([date, count]) => ({
      date,
      label: new Date(date).getMonth() + 1 + '/' + new Date(date).getDate(),
      count
    }))
})

const maxTimeCount = computed(() => {
  return Math.max(...timeStats.value.map(s => s.count), 1)
})

// 相关度分布
const scoreStats = computed(() => {
  const ranges = [
    { range: '90-100%', min: 0.9, max: 1.0, count: 0 },
    { range: '80-90%', min: 0.8, max: 0.9, count: 0 },
    { range: '70-80%', min: 0.7, max: 0.8, count: 0 },
    { range: '60-70%', min: 0.6, max: 0.7, count: 0 },
    { range: '<60%', min: 0, max: 0.6, count: 0 }
  ]
  
  props.documents.forEach(doc => {
    if (doc.relevance_score) {
      const range = ranges.find(r => doc.relevance_score! >= r.min && doc.relevance_score! < r.max)
      if (range) range.count++
    }
  })
  
  return ranges.filter(r => r.count > 0)
})

const maxScoreCount = computed(() => {
  return Math.max(...scoreStats.value.map(s => s.count), 1)
})

// 统计概览
const totalCount = computed(() => props.documents.length)

const sourceCount = computed(() => {
  return new Set(props.documents.map(d => d.source)).size
})

const avgScore = computed(() => {
  const scores = props.documents
    .map(d => d.relevance_score)
    .filter(s => s !== undefined && s !== null) as number[]
  console.log('计算平均分数:', {
    totalDocs: props.documents.length,
    validScores: scores.length,
    scores: scores,
    firstDoc: props.documents[0]
  })
  if (scores.length === 0) return 0
  const avg = scores.reduce((sum, s) => sum + s, 0) / scores.length
  return Math.round(avg * 100)
})

const weekCount = computed(() => {
  const weekAgo = new Date()
  weekAgo.setDate(weekAgo.getDate() - 7)
  return props.documents.filter(d => new Date(d.created_at) >= weekAgo).length
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
