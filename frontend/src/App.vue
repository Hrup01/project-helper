<script setup>
import { computed, nextTick, ref } from 'vue'
import { Bot, BrainCircuit, CheckCircle2, FileCode2, Loader2, MessageSquareText, RefreshCw, Search, Send, TerminalSquare, XCircle } from 'lucide-vue-next'
import { marked } from 'marked'
import hljs from 'highlight.js'
import 'highlight.js/styles/github-dark.css'

marked.setOptions({
  highlight(code, lang) {
    const language = hljs.getLanguage(lang) ? lang : 'plaintext'
    return hljs.highlight(code, { language }).value
  }
})

const repoUrl = ref('https://github.com/tiangolo/fastapi')
const force = ref(false)
const projectId = ref('')
const status = ref('idle')
const progress = ref([])
const report = ref('')
const error = ref('')
const question = ref('')
const chatMessages = ref([])
const chatStreaming = ref(false)
const reportRef = ref(null)

const renderedReport = computed(() => report.value ? marked(report.value) : '')
const canAnalyze = computed(() => repoUrl.value.trim().startsWith('https://github.com/'))

function pushProgress(type, message) {
  progress.value.push({ type, message, time: new Date().toLocaleTimeString() })
}

async function analyze() {
  if (!canAnalyze.value || status.value === 'running') return
  status.value = 'running'
  error.value = ''
  report.value = ''
  progress.value = []
  chatMessages.value = []
  pushProgress('progress', '已提交分析任务')

  try {
    const response = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ repo_url: repoUrl.value.trim(), force: force.value })
    })
    if (!response.ok) throw new Error(await response.text())
    const data = await response.json()
    projectId.value = data.project_id
    const events = new EventSource(`/api/analyze/${data.project_id}/events?repo_url=${encodeURIComponent(repoUrl.value.trim())}&force=${force.value}`)
    events.onmessage = async (event) => {
      const payload = JSON.parse(event.data)
      if (payload.type === 'progress' || payload.type === 'cached') {
        pushProgress(payload.type, payload.message)
      }
      if (payload.type === 'done') {
        report.value = payload.report
        status.value = 'completed'
        pushProgress('done', '分析完成')
        events.close()
        await nextTick()
        reportRef.value?.scrollTo({ top: 0, behavior: 'smooth' })
      }
      if (payload.type === 'error') {
        error.value = payload.message
        status.value = 'failed'
        pushProgress('error', payload.message)
        events.close()
      }
    }
    events.onerror = () => {
      if (status.value === 'running') {
        error.value = '进度连接中断，请确认后端服务正在运行。'
        status.value = 'failed'
      }
      events.close()
    }
  } catch (err) {
    error.value = err.message
    status.value = 'failed'
    pushProgress('error', err.message)
  }
}

async function ask() {
  const text = question.value.trim()
  if (!text || !projectId.value || chatStreaming.value) return
  question.value = ''
  chatMessages.value.push({ role: 'user', content: text })
  const assistant = { role: 'assistant', content: '', tools: [] }
  chatMessages.value.push(assistant)
  chatStreaming.value = true

  try {
    const response = await fetch(`/api/projects/${projectId.value}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: text })
    })
    if (!response.ok || !response.body) throw new Error(await response.text())
    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''
    while (true) {
      const { value, done } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const chunks = buffer.split('\n\n')
      buffer = chunks.pop() || ''
      for (const raw of chunks) {
        if (!raw.startsWith('data:')) continue
        const payload = JSON.parse(raw.slice(5).trim())
        if (payload.type === 'delta') assistant.content += payload.content
        if (payload.type === 'tool') assistant.tools.push(payload.message)
        if (payload.type === 'error') {
          assistant.content += `\n\n${payload.message}`
          chatStreaming.value = false
        }
        if (payload.type === 'done') {
          chatStreaming.value = false
        }
      }
    }
  } catch (err) {
    assistant.content += `\n\n请求失败：${err.message}`
  } finally {
    chatStreaming.value = false
  }
}
</script>

<template>
  <main class="app-shell">
    <section class="topbar">
      <div class="brand">
        <div class="brand-mark"><BrainCircuit :size="24" /></div>
        <div>
          <h1>Project Helper</h1>
          <p>项目学习助手 · 源码地图、报告和问答</p>
        </div>
      </div>
      <div class="status-pill" :class="status">
        <Loader2 v-if="status === 'running'" class="spin" :size="16" />
        <CheckCircle2 v-else-if="status === 'completed'" :size="16" />
        <XCircle v-else-if="status === 'failed'" :size="16" />
        <TerminalSquare v-else :size="16" />
        <span>{{ status }}</span>
      </div>
    </section>

    <section class="control-band">
      <label class="repo-input">
        <Search :size="18" />
        <input v-model="repoUrl" placeholder="输入 GitHub 仓库地址，例如 https://github.com/vuejs/vue" @keydown.enter="analyze" />
      </label>
      <label class="toggle">
        <input v-model="force" type="checkbox" />
        <span>重新分析</span>
      </label>
      <button class="primary" :disabled="!canAnalyze || status === 'running'" @click="analyze">
        <RefreshCw v-if="status !== 'running'" :size="18" />
        <Loader2 v-else class="spin" :size="18" />
        <span>分析项目</span>
      </button>
    </section>

    <p v-if="error" class="error-line">{{ error }}</p>

    <section class="workspace">
      <aside class="rail">
        <div class="panel-title">
          <FileCode2 :size="18" />
          <span>分析进度</span>
        </div>
        <ol class="timeline">
          <li v-for="(item, index) in progress" :key="index" :class="item.type">
            <span class="dot"></span>
            <div>
              <time>{{ item.time }}</time>
              <p>{{ item.message }}</p>
            </div>
          </li>
        </ol>
      </aside>

      <section ref="reportRef" class="report-pane">
        <div v-if="!report" class="empty-state">
          <Bot :size="48" />
          <h2>输入仓库地址开始分析</h2>
          <p>系统会克隆仓库、扫描源码、识别技术栈，并生成适合初学者阅读的完整报告。</p>
        </div>
        <article v-else class="markdown-body" v-html="renderedReport"></article>
      </section>

      <aside class="chat-pane">
        <div class="panel-title">
          <MessageSquareText :size="18" />
          <span>源码问答</span>
        </div>
        <div class="messages">
          <div v-if="!chatMessages.length" class="hint">
            先完成一次分析，然后询问“入口文件在哪里”“请求流程怎么走”“这个模块怎么改”。
          </div>
          <div v-for="(message, index) in chatMessages" :key="index" class="message" :class="message.role">
            <div v-if="message.tools?.length" class="tool-log">
              <p v-for="tool in message.tools" :key="tool">{{ tool }}</p>
            </div>
            <div v-if="message.role === 'assistant'" class="markdown-lite" v-html="marked(message.content || '思考中...')"></div>
            <p v-else>{{ message.content }}</p>
          </div>
        </div>
        <form class="ask-box" @submit.prevent="ask">
          <textarea v-model="question" :disabled="!projectId || chatStreaming" placeholder="向 Agent 提问，让它自主查源码回答" rows="3"></textarea>
          <button :disabled="!question.trim() || !projectId || chatStreaming">
            <Send :size="17" />
          </button>
        </form>
      </aside>
    </section>
  </main>
</template>
