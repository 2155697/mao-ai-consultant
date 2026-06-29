import { useState, useRef, useCallback, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Send, Flame, CircleDot, Menu, X, Bot } from 'lucide-react'
import type {
  ChatMessage,
  ThinkingStreamEvent,
  CognitiveGraph,
  MaoQuote,
  ChatChunk,
} from '../types'
import MessageBubble from './MessageBubble'
import WelcomeScreen from './WelcomeScreen'
import ThinkingStream from './ThinkingStream'
import CognitiveGraphComponent from './CognitiveGraph'
import MaoQuoteCard from './MaoQuoteCard'

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

let messageIdCounter = 0
function generateId(): string {
  messageIdCounter += 1
  return `${Date.now()}-${messageIdCounter}`
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [inputValue, setInputValue] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isConnected, setIsConnected] = useState(false)
  const [showSidebar, setShowSidebar] = useState(false)

  const [thinkingEvents, setThinkingEvents] = useState<ThinkingStreamEvent[]>([])
  const [cognitiveGraph, setCognitiveGraph] = useState<CognitiveGraph | null>(null)
  const [maoQuotes, setMaoQuotes] = useState<MaoQuote[]>([])

  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const eventSourceRef = useRef<EventSource | null>(null)
  const assistantContentRef = useRef<string>('')
  const cleanupTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const currentAssistantMessageIdRef = useRef<string | null>(null)
  const isStreamingRef = useRef(false)

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [])

  useEffect(() => {
    scrollToBottom()
  }, [messages, thinkingEvents, scrollToBottom])

  useEffect(() => {
    return () => {
      if (eventSourceRef.current) eventSourceRef.current.close()
      if (cleanupTimeoutRef.current) clearTimeout(cleanupTimeoutRef.current)
    }
  }, [])

  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto'
      inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 120)}px`
    }
  }, [inputValue])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleNewChat = () => {
    setMessages([])
    setThinkingEvents([])
    setCognitiveGraph(null)
    setMaoQuotes([])
    setInputValue('')
    assistantContentRef.current = ''
    currentAssistantMessageIdRef.current = null
    isStreamingRef.current = false
    setIsLoading(false)
    if (eventSourceRef.current) {
      eventSourceRef.current.close()
      eventSourceRef.current = null
    }
    if (cleanupTimeoutRef.current) clearTimeout(cleanupTimeoutRef.current)
  }

  const handleSendMessage = useCallback((text: string) => {
    if (!text.trim() || isLoading) return

    const userMessage: ChatMessage = {
      id: generateId(),
      role: 'user',
      content: text.trim(),
      timestamp: new Date().toISOString(),
    }

    setMessages(prev => [...prev, userMessage])
    setInputValue('')
    setIsLoading(true)
    setIsConnected(true)

    setThinkingEvents([])
    setCognitiveGraph(null)
    setMaoQuotes([])
    assistantContentRef.current = ''
    isStreamingRef.current = true

    const assistantId = generateId()
    currentAssistantMessageIdRef.current = assistantId
    setMessages(prev => [...prev, {
      id: assistantId,
      role: 'assistant',
      content: '',
      timestamp: new Date().toISOString(),
    }])

    connectSSE(text.trim(), [...messages, userMessage])
  }, [isLoading, messages])

  const handleSend = () => handleSendMessage(inputValue)

  const connectSSE = (messageText: string, history: ChatMessage[]) => {
    if (eventSourceRef.current) eventSourceRef.current.close()

    fetch(`${API_BASE}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify({
        message: messageText,
        history: history.slice(-10),
      }),
    })
    .then(response => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      if (!response.body) throw new Error('No body')

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      const readChunk = (): Promise<void> => {
        return reader.read().then(({ done, value }) => {
          if (done) { finalizeStream(); return }
          buffer += decoder.decode(value, { stream: true })
          const lines = buffer.split('\n')
          buffer = lines.pop() || ''

          for (const line of lines) {
            if (line.startsWith('data: ')) {
              const dataStr = line.slice(6)
              if (dataStr === '[DONE]') { finalizeStream(); return }
              try {
                const parsed: ChatChunk = JSON.parse(dataStr)
                handleSSEChunk(parsed)
              } catch {
                if (dataStr.trim()) appendContent(dataStr.trim())
              }
            }
          }
          return readChunk()
        })
      }
      return readChunk()
    })
    .catch((error) => {
      handleError(error instanceof Error ? error.message : '未知错误')
    })
  }

  const handleSSEChunk = (chunk: ChatChunk) => {
    switch (chunk.type) {
      case 'thinking_stream':
        if (chunk.thinking_step) {
          handleThinkingStep(chunk.thinking_step)
        } else if (chunk.data) {
          addThinkingEvent({
            id: generateId(),
            text: chunk.data,
            emotion: 'thinking',
            is_revert: false,
            timestamp: new Date().toISOString(),
          })
        }
        break
      case 'cognitive_structure':
        if (chunk.data) {
          try { setCognitiveGraph(JSON.parse(chunk.data)) } catch {}
        }
        break
      case 'mao_quote':
        if (chunk.data) {
          try { addQuote(JSON.parse(chunk.data)) } catch { addQuote({ text: chunk.data, source: '毛选' }) }
        }
        break
      case 'content':
        if (chunk.data) appendContent(chunk.data)
        break
      case 'done':
        finalizeStream()
        break
      case 'error':
        handleError(chunk.data || '未知错误')
        break
    }
  }

  const handleThinkingStep = (step: { id: string; name: string; content?: string; status?: string }) => {
    if (step.status === 'revert' || step.status === 'reverted') {
      setThinkingEvents(prev => {
        const existing = prev.find(e => e.id === step.id)
        if (existing) {
          return prev.map(e => e.id === step.id ? { ...e, is_revert: true, emotion: 'revert' } : e)
        }
        return [...prev, {
          id: step.id,
          text: step.content || `回溯: ${step.name}`,
          emotion: 'revert',
          is_revert: true,
          timestamp: new Date().toISOString(),
        }]
      })
    } else {
      addThinkingEvent({
        id: step.id,
        text: step.content || step.name,
        emotion: inferEmotion(step.name),
        is_revert: false,
        timestamp: new Date().toISOString(),
      })
    }
  }

  const inferEmotion = (stepName: string): string => {
    const name = stepName.toLowerCase()
    if (name.includes('矛盾') || name.includes('分析')) return 'analysis'
    if (name.includes('突破') || name.includes('解决')) return 'breakthrough'
    if (name.includes('洞察') || name.includes('发现')) return 'insight'
    if (name.includes('质疑') || name.includes('反思')) return 'doubt'
    if (name.includes('回溯') || name.includes('撤销')) return 'revert'
    if (name.includes('坚定') || name.includes('确定')) return 'determination'
    if (name.includes('搜索') || name.includes('查找')) return 'searching'
    return 'thinking'
  }

  const addThinkingEvent = (event: ThinkingStreamEvent) => {
    setThinkingEvents(prev => {
      if (prev.length > 0) {
        const last = prev[prev.length - 1]
        if (last.text === event.text && last.emotion === event.emotion) return prev
      }
      return [...prev, event]
    })
  }

  const addQuote = (quote: MaoQuote) => {
    setMaoQuotes(prev => prev.some(q => q.text === quote.text) ? prev : [...prev, quote])
  }

  const appendContent = (data: string) => {
    assistantContentRef.current += data
    const currentId = currentAssistantMessageIdRef.current
    if (currentId) {
      setMessages(prev => prev.map(msg => msg.id === currentId ? { ...msg, content: assistantContentRef.current } : msg))
    }
  }

  const finalizeStream = () => {
    if (!isStreamingRef.current) return
    isStreamingRef.current = false
    setIsLoading(false)
    if (cleanupTimeoutRef.current) clearTimeout(cleanupTimeoutRef.current)
    cleanupTimeoutRef.current = setTimeout(() => { currentAssistantMessageIdRef.current = null }, 500)
  }

  const handleError = (errorMessage: string) => {
    isStreamingRef.current = false
    setIsLoading(false)
    setIsConnected(false)
    const currentId = currentAssistantMessageIdRef.current
    if (currentId) {
      setMessages(prev => prev.map(msg => msg.id === currentId ? { ...msg, content: `抱歉，发生了错误: ${errorMessage}` } : msg))
    }
    if (cleanupTimeoutRef.current) { clearTimeout(cleanupTimeoutRef.current); cleanupTimeoutRef.current = null }
  }

  const hasMessages = messages.length > 0

  return (
    <div className="flex h-screen bg-dark-950 overflow-hidden">
      <AnimatePresence>
        {showSidebar && (
          <>
            <motion.div
              initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/60 z-40 lg:hidden"
              onClick={() => setShowSidebar(false)}
            />
            <motion.div
              initial={{ x: -300 }} animate={{ x: 0 }} exit={{ x: -300 }}
              transition={{ type: 'spring', damping: 25, stiffness: 200 }}
              className="fixed lg:static left-0 top-0 h-full w-72 bg-dark-900 border-r border-dark-800 z-50 flex flex-col"
            >
              <div className="p-4 border-b border-dark-800 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Flame size={20} className="text-mao-500" />
                  <span className="font-serif font-bold text-dark-200">历史对话</span>
                </div>
                <button onClick={() => setShowSidebar(false)} className="lg:hidden p-1.5 rounded-lg hover:bg-dark-800 text-dark-400">
                  <X size={18} />
                </button>
              </div>
              <div className="flex-1 overflow-y-auto p-3 space-y-2">
                {messages.filter(m => m.role === 'user').length === 0 ? (
                  <div className="text-center text-dark-600 text-sm mt-8">暂无对话记录</div>
                ) : (
                  messages.filter(m => m.role === 'user').map((msg, i) => (
                    <button key={msg.id} onClick={() => setShowSidebar(false)}
                      className="w-full text-left p-3 rounded-lg bg-dark-800/50 border border-dark-800 hover:border-mao-900/50 hover:bg-mao-950/20 transition-all group">
                      <div className="text-xs text-dark-500 group-hover:text-dark-400 mb-1">对话 {i + 1}</div>
                      <div className="text-sm text-dark-300 group-hover:text-dark-200 line-clamp-2">{msg.content}</div>
                    </button>
                  ))
                )}
              </div>
              <div className="p-4 border-t border-dark-800">
                <button onClick={handleNewChat}
                  className="w-full flex items-center justify-center gap-2 py-2.5 rounded-lg bg-mao-900/30 border border-mao-800/50 text-mao-300 hover:bg-mao-900/50 hover:text-mao-200 transition-all text-sm font-medium">
                  <Bot size={16} /> 新建对话
                </button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="flex-shrink-0 flex items-center gap-3 px-4 py-3 border-b border-dark-800/60 bg-dark-950/90 backdrop-blur-sm z-30">
          <button onClick={() => setShowSidebar(!showSidebar)} className="p-2 rounded-lg hover:bg-dark-800 text-dark-400 transition-colors">
            <Menu size={20} />
          </button>
          <div className="flex items-center gap-3 flex-1 min-w-0">
            <div className="relative flex-shrink-0 w-9 h-9 rounded-full bg-mao-950 border border-mao-700 flex items-center justify-center">
              <Flame size={18} className="text-gold-400 relative z-10" />
              {isLoading && <span className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-emerald-500 border-2 border-dark-950" />}
            </div>
            <div className="min-w-0">
              <h1 className="text-sm font-bold font-serif text-dark-100 truncate">教员AI咨询</h1>
              <div className="flex items-center gap-1.5">
                <CircleDot size={10} className={isConnected ? 'text-emerald-500' : isLoading ? 'text-gold-500' : 'text-dark-600'} />
                <span className="text-xs text-dark-500">{isLoading ? '思考中...' : isConnected ? '已连接' : '就绪'}</span>
              </div>
            </div>
          </div>
          <div className="hidden sm:flex items-center gap-1.5">
            {thinkingEvents.length > 0 && <span className="text-[10px] px-2 py-0.5 rounded-full bg-mao-950 border border-mao-900 text-mao-400">思考 {thinkingEvents.length}</span>}
            {cognitiveGraph && cognitiveGraph.nodes.length > 0 && <span className="text-[10px] px-2 py-0.5 rounded-full bg-gold-950 border border-gold-900 text-gold-400">结构 {cognitiveGraph.nodes.length}</span>}
            {maoQuotes.length > 0 && <span className="text-[10px] px-2 py-0.5 rounded-full bg-purple-950 border border-purple-900 text-purple-400">引用 {maoQuotes.length}</span>}
          </div>
        </header>

        <main className="flex-1 overflow-y-auto overflow-x-hidden">
          {!hasMessages ? (
            <WelcomeScreen onQuickAsk={handleSendMessage} />
          ) : (
            <div className="max-w-4xl mx-auto px-4 py-6 space-y-6">
              {messages.map((message) => (
                <MessageBubble key={message.id} message={message} isLatest={message.role === 'assistant' && isLoading && message.id === currentAssistantMessageIdRef.current} />
              ))}
              <AnimatePresence>
                {(thinkingEvents.length > 0 || cognitiveGraph || maoQuotes.length > 0) && (
                  <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} className="grid grid-cols-1 lg:grid-cols-3 gap-4">
                    {thinkingEvents.length > 0 && <div className="lg:col-span-1"><ThinkingStream events={thinkingEvents} /></div>}
                    {cognitiveGraph && cognitiveGraph.nodes.length > 0 && <div className="lg:col-span-1"><CognitiveGraphComponent graph={cognitiveGraph} /></div>}
                    {maoQuotes.length > 0 && <div className="lg:col-span-1"><MaoQuoteCard quotes={maoQuotes} /></div>}
                  </motion.div>
                )}
              </AnimatePresence>
              <div ref={messagesEndRef} />
            </div>
          )}
        </main>

        <footer className="flex-shrink-0 border-t border-dark-800/60 bg-dark-950/90 backdrop-blur-sm">
          <div className="max-w-4xl mx-auto px-4 py-3">
            <div className="flex items-end gap-2">
              <div className="flex-1 relative">
                <textarea
                  ref={inputRef}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={isLoading ? '教员正在思考...' : '输入你的问题，向教员请教...'}
                  disabled={isLoading}
                  rows={1}
                  className="w-full rounded-xl px-4 py-3 pr-10 bg-dark-900 border border-dark-700 text-dark-200 text-sm placeholder:text-dark-600 focus:outline-none focus:border-mao-700 focus:ring-1 focus:ring-mao-700/30 disabled:opacity-50 disabled:cursor-not-allowed resize-none min-h-[44px] max-h-[120px] transition-all"
                />
              </div>
              <motion.button
                onClick={handleSend}
                disabled={isLoading || !inputValue.trim()}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="flex-shrink-0 flex items-center justify-center w-11 h-11 rounded-xl bg-mao-700 text-white disabled:opacity-30 disabled:cursor-not-allowed hover:bg-mao-600 transition-colors shadow-lg shadow-mao-900/20"
              >
                <Send size={18} />
              </motion.button>
            </div>
            <div className="mt-2 text-center text-[11px] text-dark-700">教员AI咨询 · 基于毛泽东思想 · AI生成的内容仅供参考</div>
          </div>
        </footer>
      </div>
    </div>
  )
}
